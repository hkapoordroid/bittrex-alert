cd /Users/hkapoor/Desktop/learning/bittrex/build

rm bittrex-biggest-movers.zip

cd /Users/hkapoor/Desktop/learning/bittrex/src

zip -r /Users/hkapoor/Desktop/learning/bittrex/build/bittrex-biggest-movers.zip *

cd /Users/hkapoor/Desktop/learning/bittrex/venv/lib/python2.7/site-packages/

zip -r /Users/hkapoor/Desktop/learning/bittrex/build/bittrex-biggest-movers.zip *

aws s3 cp /Users/hkapoor/Desktop/learning/bittrex/build/bittrex-biggest-movers.zip s3://bittrex-alerts-lambda/bittrex-biggest-movers.zip --storage-clas STANDARD_IA

aws lambda update-function-code --function-name bittrex-biggest-movers --s3-bucket bittrex-alerts-lambda --s3-key bittrex-biggest-movers.zip
