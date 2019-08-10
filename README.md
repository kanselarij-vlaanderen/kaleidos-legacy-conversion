# Kaleidos legacy conversion

- Make sure the folder structure & naming of the doris input data corresponds to the tree listed in `doc/doris/export_dir_structure.txt` and move the contents of this tree into `./data/doris` or docker-mount it accordingly during the following operations.
- Make sure that `./data/nieuwsberichten` contains the sql dump of the nieuwsberichten-database or mount accordingly.

### Preprocessing: fix encoding issues

Fix the encoding issues of each `metadata.csv`-file recursively found in `./data/doris`.
The original `metadata.csv`-files are kept intact, new `metadata_enc_fixes.csv` files are created aside them.
```
docker build -t "encoding-fixes" ./src/encoding_fixes
docker run -v $PWD/data/doris:/data encoding-fixes
```
### Extract file metadata from pdfs

```
docker build -t "metadata-extraction" ./src/pdf_metadata_extractor
find ./data/doris -type d -print
```
Run the extraction for each folder in `./data/doris` that contains a batch of pdf-files.
Make sure to give eacht output file the `.csv` extension.
All output files should reside in `/data/output`.  

Example:
```
docker run --rm -v $PWD/data/doris:/data/input -v $PWD/data/tmp/file_metadata:/data/output \
  metadata-extraction /data/input/path-to-pdfs-folder /data/output/metadata-1.csv
```

### Running the conversion tool

Building the container image for the tool will happen automatically when spinning up docker compose.  
Environment variables worth mentioning:
- `LOG_LEVEL`: one of the python log level names (uppercase)
- `KALEIDOS_SHARE_EXPORT_SUBFOLDER`: location within the eventual app's share folder that will contain the contents of `./data/doris`. Something like `doris_exports/2019xxxx` suggested. 

Get the required containers running:
```
docker-compose up
```

Create dump of all mu-file objects: 
```
docker-compose exec convertor ./create_dump.sh create_file_dump.py
```

Create a dump for VR: 
```
docker-compose exec convertor ./create_dump.sh create_vr_dump.py
```

Create a dump for OC: 
```
docker-compose convertor ./create_dump.sh create_oc_dump.py
```
