for F in $(cat ./location_ids.txt) ; do
  echo Mining $F
  path="./data/$F/"
  mkdir $path
  python fast-instagram-scraper.py $F location --out_dir $path --save_media --since_timestamp 1483228800
  echo Done!
done;
echo Finished :\)
