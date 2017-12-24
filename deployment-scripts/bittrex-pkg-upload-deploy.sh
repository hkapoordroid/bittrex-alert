cd /Users/hkapoor/Desktop/learning/bittrex/build

rm bittrex-alerts.zip

cd /Users/hkapoor/Desktop/learning/bittrex/src

zip -r /Users/hkapoor/Desktop/learning/bittrex/build/bittrex-alerts.zip *

cd /Users/hkapoor/Desktop/learning/bittrex/venv/lib/python2.7/site-packages/

zip -r /Users/hkapoor/Desktop/learning/bittrex/build/bittrex-alerts.zip *

aws s3 cp /Users/hkapoor/Desktop/learning/bittrex/build/bittrex-alerts.zip s3://bittrex-alerts-lambda/bittrex-alerts.zip --storage-clas STANDARD_IA

aws lambda update-function-code --function-name bittrex-alerts --s3-bucket bittrex-alerts-lambda --s3-key bittrex-alerts.zip
