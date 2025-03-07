
```
#!/bin/bash

# Configure Java module access for ALL required packages based on your error logs
export JAVA_TOOL_OPTIONS="--add-opens=java.base/java.lang=ALL-UNNAMED \
--add-opens=java.base/java.util=ALL-UNNAMED \
--add-opens=java.base/java.time=ALL-UNNAMED \
--add-opens=java.base/java.io=ALL-UNNAMED \
--add-opens=java.base/java.util.concurrent=ALL-UNNAMED \
--add-opens=java.base/java.util.stream=ALL-UNNAMED \
--add-opens=java.base/java.nio=ALL-UNNAMED \
--add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED \
--add-opens=java.base/java.util.AbstractList=ALL-UNNAMED \
--add-opens=java.base/java.util.ArrayList=ALL-UNNAMED \
--add-opens=java.base/java.io.InputStreamReader=ALL-UNNAMED \
--add-opens=java.base/java.io.BufferedReader=ALL-UNNAMED"

# Run the specific test
./gradlew test --tests "com.coupang.retail.open.api.app.converter.RetailProductV2ConverterTest"
```
