#!/usr/bin/env bash
# किसी भी एरर आने पर स्क्रिप्ट को तुरंत रोकने के लिए
set -o errexit

echo "--- Installing pip dependencies ---"
 
python -m pip install --upgrade pip setuptools

 
pip install -r requirements.txt

echo "--- Collecting Static Files ---"
 
python manage.py collectstatic --no-input

echo "--- Running Database Migrations ---"
 
python manage.py makemigrations

python manage.py migrate

echo "--- Build Process Completed Successfully! ---"
