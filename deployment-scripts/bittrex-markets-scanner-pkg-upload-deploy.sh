cd /Users/hkapoor/Desktop/learning/bittrex/build

rm bittrex-market-scanner.zip

cd /Users/hkapoor/Desktop/learning/bittrex/src

zip -r /Users/hkapoor/Desktop/learning/bittrex/build/bittrex-market-scanner.zip *

cd /Users/hkapoor/Desktop/learning/bittrex/venv/lib/python2.7/site-packages/

zip -r /Users/hkapoor/Desktop/learning/bittrex/build/bittrex-market-scanner.zip *

aws s3 cp /Users/hkapoor/Desktop/learning/bittrex/build/bittrex-market-scanner.zip s3://bittrex-alerts-lambda/bittrex-market-scanner.zip --storage-clas STANDARD_IA

aws lambda update-function-code --function-name bittrex-market-scanner --s3-bucket bittrex-alerts-lambda --s3-key bittrex-market-scanner.zip
