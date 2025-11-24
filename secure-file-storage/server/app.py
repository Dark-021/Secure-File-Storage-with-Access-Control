# app.py - Flask server integrating bloom + trie + MongoDB + MinIO
from flask import Flask, request, jsonify, send_file
import os, io, base64
from pymongo import MongoClient
import boto3
from wrapper import Bloom, Trie
from utils import gen_dek, encrypt_bytes, decrypt_bytes
from bson import ObjectId

app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Config - change keys if needed
MONGO_URI = "mongodb://localhost:27017"
client = MongoClient(MONGO_URI)
db = client['sfs_db']
files_col = db['files']
audit_col = db['audit']

S3_ENDPOINT = "http://127.0.0.1:9000"
S3_ACCESS = "minioadmin"
S3_SECRET = "minioadmin"
BUCKET = "files"

s3 = boto3.client('s3', endpoint_url=S3_ENDPOINT,
                  aws_access_key_id=S3_ACCESS, aws_secret_access_key=S3_SECRET)

# In-memory algorithm instances (demo)
bloom = Bloom(m_bits=8*1024*8, k=6)  # ~64KB bit array
trie = Trie()

# Simple user simulator
def get_user():
    u = request.args.get('user') or 'guest'
    # For demo: users starting with 'f' are finance dept
    dept = 'finance' if u.startswith('f') else 'eng'
    clearance = 3 if u == 'admin' else 2
    return {'id':u, 'department':dept, 'clearance':clearance}

# Ensure bucket exists
try:
    s3.create_bucket(Bucket=BUCKET)
except Exception:
    pass

@app.route('/')
def index():
    return app.send_static_file('index.html')

# 1) Create metadata + generate DEK and respond with file_id for upload
@app.route('/files', methods=['POST'])
def create_file():
    user = get_user()
    data = request.json
    filename = data.get('filename')
    sha256 = data.get('sha256')
    sensitivity = int(data.get('sensitivity', 1))

    if not filename or not sha256:
        return jsonify({'error':'missing fields'}), 400

    # Bloom check
    maybe = bloom.check(sha256)
    if maybe:
        # exact DB check
        found = files_col.find_one({'sha256': sha256})
        if found:
            return jsonify({'status':'exists','file_id': str(found['_id'])}), 200

    # create file doc and generate per-file DEK (demo: store base64 dek - not production)
    dek = gen_dek()
    enc_dek_b64 = base64.b64encode(dek).decode('utf-8')

    doc = {'owner': user['id'], 'filename': filename, 'sha256': sha256,
           'sensitivity': sensitivity, 'enc_dek': enc_dek_b64}
    res = files_col.insert_one(doc)
    fid = str(res.inserted_id)

    # update bloom + trie
    bloom.add(sha256)
    trie.insert(filename)

    return jsonify({'file_id': fid, 'upload_key': fid}), 201

# 2) upload blob (expects ciphertext bytes)
@app.route('/upload_blob/<file_id>', methods=['PUT'])
def upload_blob(file_id):
    data = request.get_data()
    # store as-is in minio bucket
    s3.put_object(Bucket=BUCKET, Key=file_id, Body=data)
    return jsonify({'status':'ok'}), 200

# 3) search filenames by prefix (uses trie)
@app.route('/search', methods=['GET'])
def search():
    q = request.args.get('q','')
    if not q:
        return jsonify({'matches':[]})
    has = trie.has_prefix(q)
    # For demo, if trie indicates prefix exists, query Mongo for matching filenames (DB authoritative)
    if not has:
        return jsonify({'matches':[]})
    # DB query for filenames starting with prefix (case-sensitive demo)
    docs = files_col.find({'filename': {'$regex': '^' + q}})
    return jsonify({'matches':[{'id': str(d['_id']), 'filename': d['filename']} for d in docs]})

# 4) download (policy check simplified)
@app.route('/download/<file_id>', methods=['GET'])
def download(file_id):
    user = get_user()
    doc = files_col.find_one({'_id': ObjectId(file_id)})
    if not doc: return jsonify({'error':'not found'}), 404

    # simple policy: same department OR clearance >= sensitivity
    user_dept = user['department']
    res_dept = doc.get('department', user_dept)  # default
    allowed = (user_dept == res_dept) or (user['clearance'] >= doc.get('sensitivity',1))
    audit_col.insert_one({'user': user['id'], 'file_id': file_id, 'action':'download', 'allowed': allowed})
    if not allowed: return jsonify({'error':'forbidden'}), 403

    obj = s3.get_object(Bucket=BUCKET, Key=file_id)
    blob = obj['Body'].read()

    # demo: server stored dek base64 and decrypts
    dek = base64.b64decode(doc['enc_dek'])
    try:
        plaintext = decrypt_bytes(dek, blob)
    except Exception as e:
        # if decryption fails, return raw blob
        plaintext = blob
    return send_file(io.BytesIO(plaintext), download_name=doc['filename'], as_attachment=True)

# 5) list audit (admin)
@app.route('/audit', methods=['GET'])
def audit():
    docs = list(audit_col.find().limit(100).sort('_id', -1))
    out = []
    for d in docs:
        d['_id'] = str(d['_id'])
        out.append(d)
    return jsonify(out)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
