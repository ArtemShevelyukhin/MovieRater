cd ../../frontend/src
pwd
python -m http.server 7000 &
echo $!
#http://localhost:7000/miniapp.html

cd ../../backend/src
uvicorn main:app --reload