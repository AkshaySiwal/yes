
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



```
#!/bin/bash

# Point to JAVA_HOME 
export JAVA_HOME=$(java -XshowSettings:properties -version 2>&1 > /dev/null | grep 'java.home' | awk '{print $3}')
echo "$JAVA_HOME"

# Add ALL needed Java module arguments
export JAVA_TOOL_OPTIONS="--add-opens=java.base/java.lang=ALL-UNNAMED \
--add-opens=java.base/java.util=ALL-UNNAMED \
--add-opens=java.base/java.time=ALL-UNNAMED \
--add-opens=java.base/java.time.temporal=ALL-UNNAMED \
--add-opens=java.base/java.time.zone=ALL-UNNAMED \
--add-opens=java.base/java.io=ALL-UNNAMED \
--add-opens=java.base/java.util.concurrent=ALL-UNNAMED \
--add-opens=java.base/java.util.stream=ALL-UNNAMED \
--add-opens=java.base/java.nio=ALL-UNNAMED \
--add-opens=java.base/java.util.concurrent.atomic=ALL-UNNAMED \
--add-opens=java.sql/java.sql=ALL-UNNAMED"

# Use -i flag to see more information
./gradlew :rs-open-api-app:test --tests "com.coupang.retail.open.api.app.converter.RetailProductV2ConverterTest" -i
```




```
dependencies {
    // Update from 1.0-groovy-2.4 to a Java 17 compatible version
    testImplementation 'org.spockframework:spock-core:2.3-groovy-3.0'
    
    // You might also need to add Groovy 3.0+ explicitly
    testImplementation 'org.codehaus.groovy:groovy-all:3.0.13'
}
```






# GIT recover
```
# First, clean up build directories properly
./gradlew clean

# Remove any untracked files Git is showing
git clean -fd

# If you want to also remove untracked directories that are ignored by Git
git clean -fdx

# If you want to revert any modified tracked files to their original state
git checkout -- .
```


# TEST

```
./gradlew clean test --debug -Dorg.gradle.jvmargs="--add-opens=java.base/java.lang=ALL-UNNAMED --add-opens=java.base/java.util=ALL-UNNAMED --add-opens=java.base/java.lang.reflect=ALL-UNNAMED"
```



# Extra

```
testImplementation("io.mockk:mockk:1.13.5")
testImplementation("io.mockk:mockk-agent-jvm:1.13.5")
```

```
ContractTemplatePageSearchConditionTest.groovy
```
```
package com.coupang.retail.contract_admin.app.web.contract.condition

import com.coupang.retail.contract_admin.app.shared.utils.SecurityUtils
import org.junit.Test
import org.junit.runner.RunWith
import org.mockito.Mock
import org.mockito.MockitoAnnotations
import org.junit.Before
import org.mockito.junit.MockitoJUnitRunner
import static org.junit.Assert.assertEquals

@RunWith(MockitoJUnitRunner.class)
class ContractTemplatePageSearchConditionTest {
    
    // If you need to mock SecurityUtils, you would use Mockito's static mocking
    // But this test doesn't actually use SecurityUtils
    
    @Before
    public void setup() {
        MockitoAnnotations.openMocks(this)
    }
    
    @Test
    public void testQueryContractListWithContractIds() {
        // Arrange
        ContractTemplatePageSearchCondition condition = ContractTemplatePageSearchCondition.builder()
            .name("hehe")
            .pageNumber(111)
            .pageSize(222)
            .build()
            
        // Assert
        assertEquals("hehe", condition.getName())
        assertEquals(111, condition.getPageNumber())
        assertEquals(222, condition.getPageSize())
    }
}
```
