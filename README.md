# Kaleidos legacy conversion


### Preprocessing: fix encoding issues

Fix the encoding issues of each `metadata.csv`-file recursively found in `./data/doris`. The original `metadata.csv`-files are kept intact, new `metadata_enc_fixes.csv` files are created.
```
docker build -t "encoding-fixes" ./src/encoding_fixes
docker run -v ./data/doris:/data encoding-fixes
```

### Running the conversion tool

building the container for the tool:

Get the required containers running:
```
docker-compose -f docker-compose.database.yml -f docker-compose.convertor.yml up
```

Create dump of all mu-file objects: 
```
docker-compose -f docker-compose.database.yml -f docker-compose.convertor.yml \
  exec convertor ./create_dump.sh create_file_dump.py
```

Create a dump for VR: 
```

docker-compose -f docker-compose.database.yml -f docker-compose.convertor.yml \
  exec convertor ./create_dump.sh create_vr_dump.py
```

Create a dump for OC: 
```
docker-compose -f docker-compose.convertor.yml \
  exec convertor ./create_dump.sh create_oc_dump.py
```
