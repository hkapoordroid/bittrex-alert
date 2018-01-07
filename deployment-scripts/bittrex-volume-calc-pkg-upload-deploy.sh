cd /Users/hkapoor/Desktop/learning/bittrex/build

rm bittrex-volume-calc.zip

cd /Users/hkapoor/Desktop/learning/bittrex/src

zip -r /Users/hkapoor/Desktop/learning/bittrex/build/bittrex-volume-calc.zip *

cd /Users/hkapoor/Desktop/learning/bittrex/venv/lib/python2.7/site-packages/

zip -r /Users/hkapoor/Desktop/learning/bittrex/build/bittrex-volume-calc.zip *

aws s3 cp /Users/hkapoor/Desktop/learning/bittrex/build/bittrex-volume-calc.zip s3://bittrex-alerts-lambda/bittrex-volume-calc.zip --storage-clas STANDARD_IA

aws lambda update-function-code --function-name bittrex-volume-calc --s3-bucket bittrex-alerts-lambda --s3-key bittrex-volume-calc.zip
