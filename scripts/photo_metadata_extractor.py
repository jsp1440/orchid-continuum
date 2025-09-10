#!/usr/bin/env python3
# Extract EXIF + basic image features; outputs a CSV showing filled fields per photo.
import os, sys, csv
from PIL import Image, ExifTags

def exif_dict(img_path):
  try:
    img = Image.open(img_path)
    exif = img.getexif() or {}
    return {ExifTags.TAGS.get(k,k):v for k,v in exif.items()}
  except Exception:
    return {}

def parse_dt(exif):
  raw = exif.get('DateTimeOriginal') or exif.get('DateTime')
  if not raw: return ''
  raw = raw.replace(':','-',2)  # 2024-05-02 14:33:10
  return raw

def dominant_color(img_path, resize=128):
  try:
    img = Image.open(img_path).convert('RGB').resize((resize, resize))
    from collections import Counter
    (r,g,b),_ = Counter(list(img.getdata())).most_common(1)[0]
    return f"({r},{g},{b})"
  except Exception:
    return ''

def main(folder):
  out_csv = os.path.join(folder, 'photo_metadata_extracted.csv')
  fields = ['file','capture_datetime_local','gps_lat','gps_lon','width','height','orientation','fnumber','iso','exposure_time','dominant_color_rgb','filled_count','total_possible']
  total_possible = len(fields)-2
  with open(out_csv,'w',newline='',encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
    for name in os.listdir(folder):
      if not name.lower().endswith(('.jpg','.jpeg','.png','.tif','.tiff')): continue
      p = os.path.join(folder,name)
      row = {k:'' for k in fields}; row['file']=name
      ex = exif_dict(p)
      row['capture_datetime_local'] = parse_dt(ex)
      gps = ex.get('GPSInfo') or {}
      def gps_coord(r):
        try:
          d=r[0][0]/r[0][1]; m=r[1][0]/r[1][1]; s=r[2][0]/r[2][1]; return d+m/60+s/3600
        except: return None
      lat = lon = None
      if gps:
        gl=gps.get(2); gr=gps.get(1); gL=gps.get(4); gR=gps.get(3)
        if gl and gL:
          lat=gps_coord(gl); lon=gps_coord(gL)
          if gr in ['S','s']: lat=-lat
          if gR in ['W','w']: lon=-lon
      row['gps_lat'] = f"{lat:.6f}" if isinstance(lat, (int, float)) and lat is not None else ''
      row['gps_lon'] = f"{lon:.6f}" if isinstance(lon, (int, float)) and lon is not None else ''
      try:
        with Image.open(p) as im: row['width'],row['height']=im.size
      except: pass
      row['orientation'] = str(ex.get('Orientation',''))
      row['fnumber']     = str(ex.get('FNumber',''))
      row['iso']         = str(ex.get('ISOSpeedRatings',''))
      row['exposure_time']=str(ex.get('ExposureTime',''))
      row['dominant_color_rgb']=dominant_color(p)
      filled = sum(1 for k in fields if k not in ['file','filled_count','total_possible'] and row.get(k) not in ['',None])
      row['filled_count']=str(filled); row['total_possible']=str(total_possible)
      w.writerow(row)
  print("Wrote:", out_csv)

if __name__ == '__main__':
  if len(sys.argv)<2:
    print("Usage: python scripts/photo_metadata_extractor.py /path/to/photos"); sys.exit(1)
  main(sys.argv[1])