
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
import org.mockito.InjectMocks
import org.mockito.Mock
import org.mockito.MockitoAnnotations
import org.mockito.junit.MockitoJUnitRunner
import static org.mockito.Mockito.*
import static org.junit.Assert.*

@RunWith(MockitoJUnitRunner.class)
public class ContractControllerTest {
    
    // Constants for test cases from the data table
    private static final String LOGIN_USER_ID_WHATEVER = "whatever"
    private static final String LOGIN_USER_ID_CREATOR = "creator"
    
    @Mock
    ContractV1Delegator contractV1Delegator;
    
    @Mock
    ContractV2Delegator contractV2Delegator;
    
    @Mock
    SirtMaskingFacade sirtMaskingFacade;
    
    @InjectMocks
    ContractController contractController;
    
    // Test data
    ContractDtoNew contractDto;
    
    @Before
    public void setup() {
        MockitoAnnotations.openMocks(this);
        
        // Initialize test data
        contractDto = new ContractDtoNew(
            partnerId: "22",
            createdBy: "creator",
            contractPartakerDto: new ContractPartakerDto(
                signerGroups: [new ContractSignerGroupDto(members: [new PartakerMemberDto(userId: "signer")])],
                approverGroups: [new ContractApproverGroupDto(members: [new PartakerMemberDto(userId: "approver")])],
                referrers: [new PartakerMemberDto(userId: "referrer")]
            )
        );
    }
    
    @Test
    public void testGetContractDetailViews_SirtPermission() {
        // Test case 1: "whatever" login ID, mask invoc count 1, has SIRT permission true, expected result OK true
        testGetContractDetailViewsWithLoginId(LOGIN_USER_ID_WHATEVER, 1, true, true);
        
        // Test case 2: "whatever" login ID, mask invoc count 1, has SIRT permission false, expected result OK false
        testGetContractDetailViewsWithLoginId(LOGIN_USER_ID_WHATEVER, 1, false, false);
        
        // Test case 3: "creator" login ID, mask invoc count 0, has SIRT permission false, expected result OK true
        testGetContractDetailViewsWithLoginId(LOGIN_USER_ID_CREATOR, 0, false, true);
    }
    
    private void testGetContractDetailViewsWithLoginId(String loginId, int maskInvocCount, 
                                                      boolean hasSirtPermission, boolean expectedResultOk) {
        // Arrange
        try (MockedStatic<SecurityUtils> mockedSecurityUtils = mockStatic(SecurityUtils.class)) {
            mockedSecurityUtils.when(() -> SecurityUtils.getCurrentLoginId()).thenReturn(loginId);
            
            // Mock contract detail view
            ContractDetailViewDtoNew detailViewDto = mock(ContractDetailViewDtoNew.class);
            when(detailViewDto.getContractDto()).thenReturn(contractDto);
            
            // Mock contract V2 delegator
            AppResponse appResponse = mock(AppResponse.class);
            when(appResponse.isOk()).thenReturn(true);
            when(appResponse.getData()).thenReturn(detailViewDto);
            when(contractV2Delegator.getContractV2Detail(anyLong(), anyLong(), anyLong())).thenReturn(appResponse);
            
            // Mock SIRT permission check
            when(sirtMaskingFacade.checkPermission(anyString())).thenReturn(hasSirtPermission);
            
            // Act
            def result = contractController.getContractDetailViews(1, "returnUrl", 0);
            
            // Assert
            assertEquals(expectedResultOk, result.isOk());
            
            // Verify interactions
            verify(sirtMaskingFacade, times(maskInvocCount)).checkPermission(anyString());
        }
    }
    
    @Test
    public void testDraftContracts_SpringUpgrade() {
        // Arrange
        ContractDraftDto contractDraftDto = new ContractDraftDto();
        contractDraftDto.setContractTypeId("111");
        
        // Act - First call without partnerId
        AppResponse<ContractDtoNew> response = contractController.draftContracts(contractDraftDto);
        
        // Assert
        assertEquals("partnerId is empty", response.getErrors().get(0).getMessage());
        
        // Act - Second call with partnerId but no title
        contractDraftDto.setPartnerId("111");
        contractDraftDto.setTitle(Maps.newHashMap());
        contractDraftDto.getTitle().put(LocUtils.getPrimaryLocale(), "");
        response = contractController.draftContracts(contractDraftDto);
        
        // Assert
        assertEquals("contract title is empty", response.getErrors().get(0).getMessage());
        
        // Act - Third call with valid data
        contractDraftDto.setPartnerId("111");
        contractDraftDto.getTitle().put(LocUtils.getPrimaryLocale(), "aaa");
        response = contractController.draftContracts(contractDraftDto);
        
        // Assert
        assertNull(response);
    }
}
```
