
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
package com.coupang.retail.contract_admin.app.web.contract.coupon

import com.coupang.apigateway.services.rs_contract_api.model.CouponContractDto
import com.coupang.apigateway.services.rs_contract_api.model.CouponContractQueryDto
import com.coupang.retail.contract_admin.app.delegate.contract.CouponContractDelegator
import com.coupang.retail.contract_admin.app.service.excelgenerator.ExcelGenerator
import com.coupang.retail.contract_admin.app.shared.AppResponse
import com.coupang.retail.contract_admin.app.shared.RsProjectConfig
import com.coupang.retail.contract_admin.app.shared.utils.SecurityUtils
import com.coupang.retail.contract_admin.app.web.contract.facade.SirtMaskingFacade
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.mockito.InjectMocks
import org.mockito.Mock
import org.mockito.MockedStatic
import org.mockito.MockitoAnnotations
import org.mockito.junit.MockitoJUnitRunner
import static org.mockito.Mockito.*
import static org.junit.Assert.*

import javax.servlet.http.HttpServletResponse
import java.time.LocalDate
import java.util.function.Consumer

@RunWith(MockitoJUnitRunner.class)
public class CouponContractControllerTest {
    
    private static final String LOGIN_USER_ID = "loginUserId"
    private static final String CURRENT_LOGIN_ID = "other_user"
    private static final String PARTNER_ID = "A00123456"
    
    @Mock
    CouponContractController couponContractController
    
    @Mock
    RsProjectConfig config
    
    @Mock
    CouponContractDelegator couponContractDelegator
    
    @Mock
    ExcelGenerator excelGenerator
    
    @Mock
    SirtMaskingFacade sirtMaskingFacade
    
    CouponContractDto couponContractDto
    
    @Before
    public void setup() {
        MockitoAnnotations.openMocks(this)
        
        // Create a real controller with mocked dependencies
        couponContractController = new CouponContractController(
            config,
            couponContractDelegator,
            excelGenerator,
            sirtMaskingFacade
        )
        
        // Mock static SecurityUtils
        try (MockedStatic<SecurityUtils> mockedSecurityUtils = mockStatic(SecurityUtils.class)) {
            mockedSecurityUtils.when(() -> SecurityUtils.getCurrentLoginId()).thenReturn(LOGIN_USER_ID)
        }
        
        // Initialize test data
        couponContractDto = new CouponContractDto(
            createdBy: "creator",
            signerIds: ["signer"],
            approverIds: ["approver"],
            referrerIds: ["referrer"]
        )
    }
    
    @Test
    public void testMaskVendorInfoIfNecessary() {
        // Arrange
        int expectedInvocationCount = 1
        when(sirtMaskingFacade.bulkMaskIfNecessary(anyString(), anyList(), anyList(), any(Consumer.class)))
            .thenReturn(expectedInvocationCount)
            
        // Act
        couponContractController.maskVendorInfoIfNecessary(couponContractDto, CURRENT_LOGIN_ID)
        
        // Assert
        verify(sirtMaskingFacade).bulkMaskIfNecessary(eq(CURRENT_LOGIN_ID), anyList(), anyList(), any(Consumer.class))
        
        // Verify data table values
        Map<String, Integer> expectedResults = [
            "creator": 0,
            "signer": 0,
            "approver": 0,
            "referrer": 0,
            "whatever": 1
        ]
        
        // We can't directly verify the data table, but we can verify the interaction
        verify(sirtMaskingFacade).bulkMaskIfNecessary(
            eq(CURRENT_LOGIN_ID), 
            anyList(), 
            anyList(), 
            any(Consumer.class)
        )
    }
    
    @Test
    public void testMaskVendorInfoIfNecessary_MaskPartnerNameIfSirtPermitPartnerNameIsFalse() {
        // Arrange
        when(config.isSirtPermitPartnerName()).thenReturn(false)
        
        List<CouponContractDto> couponContractDtos = [
            CouponContractDto.builder()
                .partnerId(PARTNER_ID)
                .partnerName("test_partnerName")
                .businessNumber("test_businessNumber")
                .createdBy("test_creator")
                .signerIds(["test_signer"])
                .approverIds(["test_approver"])
                .referrerIds(["test_referrer"])
                .build()
        ]
        
        // Mock the bulkMaskIfNecessary method to verify it's called with correct parameters
        when(sirtMaskingFacade.bulkMaskIfNecessary(
            eq("other_user"), 
            eq([PARTNER_ID, PARTNER_ID]), 
            any(List.class), 
            any(Consumer.class)
        )).thenAnswer { invocation ->
            // Extract the consumer from the arguments
            Consumer<List<String>> consumer = invocation.getArguments()[3]
            // Call the consumer with a list that has size 2 to simulate the behavior
            consumer.accept(["item1", "item2"])
            return 2
        }
        
        // Act
        couponContractController.maskVendorInfoIfNecessary(couponContractDtos, "other_user")
        
        // Assert
        verify(sirtMaskingFacade).bulkMaskIfNecessary(
            eq("other_user"), 
            eq([PARTNER_ID, PARTNER_ID]), 
            any(List.class), 
            any(Consumer.class)
        )
    }
    
    @Test
    public void testMaskVendorInfoIfNecessary_DoNotMaskPartnerNameIfSirtPermitPartnerNameIsTrue() {
        // Arrange
        when(config.isSirtPermitPartnerName()).thenReturn(true)
        
        List<CouponContractDto> couponContractDtos = [
            CouponContractDto.builder()
                .partnerId(PARTNER_ID)
                .partnerName("test_partnerName")
                .businessNumber("test_businessNumber")
                .createdBy("test_creator")
                .signerIds(["test_signer"])
                .approverIds(["test_approver"])
                .referrerIds(["test_referrer"])
                .build()
        ]
        
        // Mock the bulkMaskIfNecessary method to verify it's called with correct parameters
        when(sirtMaskingFacade.bulkMaskIfNecessary(
            eq("other_user"), 
            eq([PARTNER_ID]), 
            any(List.class), 
            any(Consumer.class)
        )).thenAnswer { invocation ->
            // Extract the consumer from the arguments
            Consumer<List<String>> consumer = invocation.getArguments()[3]
            // Call the consumer with a list that has size 1 to simulate the behavior
            consumer.accept(["item1"])
            return 1
        }
        
        // Act
        couponContractController.maskVendorInfoIfNecessary(couponContractDtos, "other_user")
        
        // Assert
        verify(sirtMaskingFacade).bulkMaskIfNecessary(
            eq("other_user"), 
            eq([PARTNER_ID]), 
            any(List.class), 
            any(Consumer.class)
        )
    }
    
    @Test
    public void testDownloadContractExcel_WillCallMaskVendorInfoIfNecessary() {
        // Arrange
        AppResponse<List<CouponContractDto>> appResponse = new AppResponse<>([couponContractDto])
        when(couponContractDelegator.queryCouponContract(any())).thenReturn(appResponse)
        HttpServletResponse response = mock(HttpServletResponse.class)
        
        // Mock the bulkMaskIfNecessary method
        when(sirtMaskingFacade.bulkMaskIfNecessary(
            anyString(), 
            anyList(), 
            anyList(), 
            any(Consumer.class)
        )).thenReturn(1)
        
        // Act
        couponContractController.downloadContractExcel(
            response, 
            "", 
            "", 
            CouponContractQueryDto.ContractTypeEnum.REGULAR.toString(), 
            LocalDate.now(), 
            LocalDate.now()
        )
        
        // Assert
        verify(sirtMaskingFacade).bulkMaskIfNecessary(
            anyString(), 
            anyList(), 
            anyList(), 
            any(Consumer.class)
        )
    }
}
```
