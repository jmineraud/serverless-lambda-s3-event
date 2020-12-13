#!/bin/bash
rm -f apply-s3-notification.zip
pip install requests -t python

find python -type d -name "tests" -exec rm -rf {}
find python -type d -name "__pycache__" -exec rm -rf {} +
rm -rf python/{caffe2,wheel,wheel-*,pkg_resources,boto*,aws*,pip,pip-*,pipenv,setuptools}
rm -rf python/{*.egg-info,*.dist-info}
find python -name \*.pyc -delete

cd python;
zip -r ../apply-s3-notification.zip .
cd ..
zip -r apply-s3-notification.zip apply_s3_notifications.py

rm -rf python/
