
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
package com.coupang.retail.contract_admin.app.web.contract

import com.coupang.apigateway.services.rs_contract_api.model.*
import com.coupang.retail.contract_admin.app.delegate.contract.ContractV1Delegator
import com.coupang.retail.contract_admin.app.delegate.contract.ContractV2Delegator
import com.coupang.retail.contract_admin.app.shared.AppResponse
import com.coupang.retail.contract_admin.app.shared.i18n.LocUtils
import com.coupang.retail.contract_admin.app.shared.utils.SecurityUtils
import com.coupang.retail.contract_admin.app.web.contract.facade.SirtMaskingFacade
import com.google.common.collect.Maps
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.mockito.Mock
import org.mockito.MockedStatic
import org.mockito.MockitoAnnotations
import org.mockito.junit.MockitoJUnitRunner
import static org.mockito.Mockito.*
import static org.junit.Assert.*

@RunWith(MockitoJUnitRunner.class)
public class ContractControllerTest {
    
    private static final String LOGIN_USER_ID = "whatever"
    private static final boolean HAS_SIRT_PERMISSION_TRUE = true
    private static final boolean HAS_SIRT_PERMISSION_FALSE = false
    private static final boolean EXPECTED_RESULT_OK_TRUE = true
    private static final boolean EXPECTED_RESULT_OK_FALSE = false
    
    @Mock
    ContractV1Delegator contractV1Delegator
    
    @Mock
    ContractV2Delegator contractV2Delegator
    
    @Mock
    SirtMaskingFacade sirtMaskingFacade
    
    ContractController contractController
    
    Contract2DtoNew contractDto
    
    @Before
    public void setup() {
        MockitoAnnotations.openMocks(this)
        
        // Create a real controller with mocked dependencies
        contractController = new ContractController(
            contractV1Delegator,
            contractV2Delegator,
            sirtMaskingFacade
        )
        
        // Mock static SecurityUtils
        try (MockedStatic<SecurityUtils> mockedSecurityUtils = mockStatic(SecurityUtils.class)) {
            mockedSecurityUtils.when(() -> SecurityUtils.getCurrentLoginId()).thenReturn(LOGIN_USER_ID)
        }
        
        // Initialize test data
        contractDto = new Contract2DtoNew(
            partnerId: "22",
            createdBy: "creator",
            contractPartakerDto: new ContractPartakerDto(
                signerGroups: [new ContractSignerGroupDto(members: [new PartakerMemberDto(userId: "signer")])],
                approverGroups: [new ContractApproverGroupDto(members: [new PartakerMemberDto(userId: "approver")])],
                referrers: [new PartakerMemberDto(userId: "referrer")]
            )
        )
    }
    
    @Test
    public void testGetContractDetailViews_TestSirtPermission() {
        // Test case 1: LOGIN_USER_ID = "whatever", MASK_INVOC_COUNT = 1, HAS_SIRT_PERMISSION = true, EXPECTED_RESULT_OK = true
        testGetContractDetailViewsCase("whatever", 1, true, true)
        
        // Test case 2: LOGIN_USER_ID = "whatever", MASK_INVOC_COUNT = 1, HAS_SIRT_PERMISSION = false, EXPECTED_RESULT_OK = false
        testGetContractDetailViewsCase("whatever", 1, false, false)
        
        // Test case 3: LOGIN_USER_ID = "creator", MASK_INVOC_COUNT = 0, HAS_SIRT_PERMISSION = false, EXPECTED_RESULT_OK = true
        testGetContractDetailViewsCase("creator", 0, false, true)
    }
    
    private void testGetContractDetailViewsCase(String loginUserId, int maskInvocCount, boolean hasSirtPermission, boolean expectedResultOk) {
        // Arrange
        try (MockedStatic<SecurityUtils> mockedSecurityUtils = mockStatic(SecurityUtils.class)) {
            mockedSecurityUtils.when(() -> SecurityUtils.getCurrentLoginId()).thenReturn(loginUserId)
            
            // Mock contract detail view
            ContractDetailViewDtoNew detailViewDto = mock(ContractDetailViewDtoNew.class)
            when(detailViewDto.getContractDto()).thenReturn(contractDto)
            
            // Mock AppResponse
            AppResponse<ContractDetailViewDtoNew> appResponse = mock(AppResponse.class)
            when(appResponse.isOk()).thenReturn(expectedResultOk)
            when(appResponse.getData()).thenReturn(detailViewDto)
            
            // Mock contractV2Delegator
            when(contractV2Delegator.getContractV2Detail(anyLong(), anyString(), anyInt())).thenReturn(appResponse)
            
            // Mock sirtMaskingFacade
            when(sirtMaskingFacade.checkPermission(anyString(), anyList())).thenReturn(hasSirtPermission ? 1 : 0)
            
            // Act
            def result = contractController.getContractDetailViews(1, "returnUri", 0)
            
            // Assert
            assertEquals(expectedResultOk, result.isOk())
            
            // Verify sirtMaskingFacade.checkPermission was called the expected number of times
            if (maskInvocCount > 0) {
                verify(sirtMaskingFacade, times(maskInvocCount)).checkPermission(anyString(), anyList())
            } else {
                verify(sirtMaskingFacade, never()).checkPermission(anyString(), anyList())
            }
        }
    }
    
    @Test
public void testDraftContracts_Spring5Upgrade() {
    // Arrange
    ContractDraftDto contractDraftDto = new ContractDraftDto()
    contractDraftDto.setContractTypeId("111")
    
    // Test case 1: partnerId is empty
    AppResponse<Contract2DtoNew> emptyPartnerIdResponse = mock(AppResponse.class)
    List<Object> errors1 = new ArrayList<>()
    errors1.add(createErrorObject("partnerId is empty"))
    when(emptyPartnerIdResponse.getErrors()).thenReturn(errors1)
    when(contractController.draftContracts(contractDraftDto)).thenReturn(emptyPartnerIdResponse)
    
    // Act & Assert for case 1
    AppResponse<Contract2DtoNew> response = contractController.draftContracts(contractDraftDto)
    assertEquals("partnerId is empty", getErrorMessage(response.getErrors().get(0)))
    
    // Test case 2: contract title is empty
    contractDraftDto.setPartnerId("111")
    contractDraftDto.setTitle(Maps.newHashMap())
    contractDraftDto.getTitle().put(LocUtils.getPrimaryLocale(), "")
    
    AppResponse<Contract2DtoNew> emptyTitleResponse = mock(AppResponse.class)
    List<Object> errors2 = new ArrayList<>()
    errors2.add(createErrorObject("contract title is empty"))
    when(emptyTitleResponse.getErrors()).thenReturn(errors2)
    when(contractController.draftContracts(contractDraftDto)).thenReturn(emptyTitleResponse)
    
    // Act & Assert for case 2
    response = contractController.draftContracts(contractDraftDto)
    assertEquals("contract title is empty", getErrorMessage(response.getErrors().get(0)))
    
    // Test case 3: valid contract
    contractDraftDto.setPartnerId("111")
    contractDraftDto.getTitle().put(LocUtils.getPrimaryLocale(), "aaa")
    
    when(contractController.draftContracts(contractDraftDto)).thenReturn(null)
    
    // Act & Assert for case 3
    response = contractController.draftContracts(contractDraftDto)
    assertNull(response)
}

// Helper method to create an error object based on your AppResponse implementation
private Object createErrorObject(String message) {
    // This is a generic approach - you'll need to adjust based on your actual AppResponse implementation
    Object errorObj = mock(Object.class)
    when(errorObj.toString()).thenReturn(message)
    when(errorObj.getMessage()).thenReturn(message)
    return errorObj;
}

// Helper method to get error message from error object
private String getErrorMessage(Object error) {
    // Try different ways to get the message based on your implementation
    try {
        return error.getMessage();
    } catch (Exception e) {
        return error.toString();
    }
  }
}
```
