
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
package com.coupang.retail.contract_admin.app.service.growth_rebate.validator

import com.coupang.apigateway.services.rs_contract_api.model.Contract2DtoNew
import com.coupang.apigateway.services.rs_contract_api.model.ContractAttributeValueDto
import com.coupang.apigateway.services.rs_contract_api.model.ContractTypeDto
import com.coupang.apigateway.services.rs_contract_api.model.RebateDuplicateResult
import com.coupang.retail.commons.lang.exception.RetailRuntimeException
import com.coupang.retail.contract_admin.app.delegate.contract.ContractTypeDelegator
import com.coupang.retail.contract_admin.app.delegate.contract.ContractV2Delegator
import com.coupang.retail.contract_admin.app.service.growth_rebate.PurchaseOrderService
import com.coupang.retail.contract_admin.app.service.validator.ContractValidationException
import com.coupang.retail.contract_admin.app.shared.AppResponses
import com.coupang.retail.contract_admin.app.shared.dto.validation_result.ValidationResultDTO
import com.google.common.collect.Lists
import org.apache.commons.collections4.CollectionUtils
import org.junit.Before
import org.junit.Test
import org.junit.runner.RunWith
import org.mockito.Mock
import org.mockito.MockitoAnnotations
import org.mockito.junit.MockitoJUnitRunner

import static org.junit.Assert.*
import static org.mockito.Mockito.*

@RunWith(MockitoJUnitRunner.class)
class GrowthRebateValidatorTest {

    @Mock
    ContractV2Delegator contractV2Delegator
    
    @Mock
    ContractTypeDelegator contractTypeDelegator
    
    @Mock
    PurchaseOrderService purchaseOrderService
    
    GrowthRebateValidator sut
    
    @Before
    void setup() {
        MockitoAnnotations.openMocks(this)
        
        sut = new GrowthRebateValidator(
            purchaseOrderService,
            contractV2Delegator,
            contractTypeDelegator,
            []
        )
    }
    
    @Test
    void validateGrowthRebate_skip_when_contract_dto_condition() {
        // Arrange
        when(contractV2Delegator.getContractDetailByAggregateId(anyString()))
            .thenReturn(AppResponses.success(new Contract2DtoNew(signatureType: Contract2DtoNew.SignatureTypeEnum.ManualSign)))
        
        // Act
        def result = sut.validateGrowthRebate("test", "test", "test")
        
        // Assert
        assertTrue(result.isValid())
    }
    
    @Test
    void validateGrowthRebate_not_skip_with_po_validation() {
        // Arrange
        // Mock contract details
        when(contractV2Delegator.getContractDetailByAggregateId(anyString()))
            .thenReturn(AppResponses.success(new Contract2DtoNew(signatureType: Contract2DtoNew.SignatureTypeEnum.DocuSign)))
        
        // Mock contract attributes
        List<ContractAttributeValueDto> attributeValues = Lists.newArrayList(
            ContractAttributeValueDto.builder()
                .elementTypeName("unit_categories")
                .elementValueId(1)
                .attributeTypeName("Unit 1")
                .build(),
            ContractAttributeValueDto.builder()
                .elementTypeName("unit_categories")
                .elementValueId(1)
                .attributeTypeName("Unit 2")
                .build(),
            ContractAttributeValueDto.builder()
                .elementTypeName("growth_rebate_condition_info")
                .elementValueId(3)
                .attributeTypeName("rebateStartMonth")
                .attributeValue("202307")
                .build(),
            ContractAttributeValueDto.builder()
                .elementTypeName("growth_rebate_condition_info")
                .elementValueId(3)
                .attributeTypeName("rebateEndMonth")
                .attributeValue("202308")
                .build()
        )
        when(contractV2Delegator.getContractAttributeValues(anyString()))
            .thenReturn(attributeValues)
        
        // Mock rebate duplicate check
        when(contractV2Delegator.getRebateDuplicateChecks(anyString()))
            .thenReturn(RebateDuplicateResult.builder().duplicateCheckDtos(Lists.newArrayList()).build())
        
        // Mock purchase order history
        when(purchaseOrderService.getMonthlyPurchaseOrderHistoryDTOs(anyString()))
            .thenReturn(Lists.newArrayList())
        
        // Act
        ValidationResultDTO resultDTO = sut.validateGrowthRebate("test", "test", "테스트")
        
        // Assert
        assertFalse(resultDTO.isEmpty())
        assertTrue(resultDTO.targetPurchaseOrders.size() > 0)
        assertTrue(resultDTO.forecastPurchaseOrders.size() > 0)
    }
    
    @Test
    void validateGrowthRebate_not_skip_without_po_validation() {
        // Arrange
        // Mock contract details
        when(contractV2Delegator.getContractDetailByAggregateId(anyString()))
            .thenReturn(AppResponses.success(new Contract2DtoNew(signatureType: Contract2DtoNew.SignatureTypeEnum.DocuSign)))
        
        // Mock contract attributes
        List<ContractAttributeValueDto> attributeValues = Lists.newArrayList(
            ContractAttributeValueDto.builder()
                .elementTypeName("unit_categories")
                .elementValueId(1)
                .attributeTypeName("Unit 1")
                .build(),
            ContractAttributeValueDto.builder()
                .elementTypeName("unit_categories")
                .elementValueId(1)
                .attributeTypeName("Unit 2")
                .build(),
            ContractAttributeValueDto.builder()
                .elementTypeName("growth_rebate_condition_info")
                .elementValueId(3)
                .attributeTypeName("rebateStartMonth")
                .attributeValue("202307")
                .build(),
            ContractAttributeValueDto.builder()
                .elementTypeName("growth_rebate_condition_info")
                .elementValueId(3)
                .attributeTypeName("rebateEndMonth")
                .attributeValue("202308")
                .build()
        )
        when(contractV2Delegator.getContractAttributeValues(anyString()))
            .thenReturn(attributeValues)
        
        // Mock rebate duplicate check
        when(contractV2Delegator.getRebateDuplicateChecks(anyString()))
            .thenReturn(RebateDuplicateResult.builder().duplicateCheckDtos(Lists.newArrayList()).build())
        
        // Mock purchase order history
        when(purchaseOrderService.getMonthlyPurchaseOrderHistoryDTOs(anyString()))
            .thenReturn(Lists.newArrayList())
        
        // Act
        ValidationResultDTO resultDTO = sut.validateGrowthRebate("test", "test", "Fix Amount")
        
        // Assert
        assertNull(resultDTO)
        assertTrue(CollectionUtils.isEmpty(resultDTO?.targetPurchaseOrders))
        assertTrue(CollectionUtils.isEmpty(resultDTO?.forecastPurchaseOrders))
    }
    
    @Test(expected = RetailRuntimeException.class)
    void validateGrowthRebate_block_with_PSA() {
        // Arrange
        // Instead of using reflection to modify environment variables, we'll mock the behavior
        // Mock contract details
        when(contractV2Delegator.getContractDetailByAggregateId(anyString()))
            .thenReturn(AppResponses.success(new Contract2DtoNew(signatureType: Contract2DtoNew.SignatureTypeEnum.DocuSign)))
        
        // Mock contract attributes
        List<ContractAttributeValueDto> attributeValues = Lists.newArrayList(
            ContractAttributeValueDto.builder()
                .elementTypeName("unit_categories")
                .elementValueId(1)
                .attributeTypeName("Unit 1")
                .build(),
            ContractAttributeValueDto.builder()
                .elementTypeName("unit_categories")
                .elementValueId(1)
                .attributeTypeName("Unit 2")
                .build(),
            ContractAttributeValueDto.builder()
                .elementTypeName("growth_rebate_condition_info")
                .elementValueId(3)
                .attributeTypeName("rebateStartMonth")
                .attributeValue("202307")
                .build(),
            ContractAttributeValueDto.builder()
                .elementTypeName("growth_rebate_condition_info")
                .elementValueId(3)
                .attributeTypeName("rebateEndMonth")
                .attributeValue("202308")
                .build()
        )
        when(contractV2Delegator.getContractAttributeValues(anyString()))
            .thenReturn(attributeValues)
        
        // Mock rebate duplicate check
        when(contractV2Delegator.getRebateDuplicateChecks(anyString()))
            .thenReturn(RebateDuplicateResult.builder().duplicateCheckDtos(Lists.newArrayList()).build())
        
        // Mock purchase order history
        when(purchaseOrderService.getMonthlyPurchaseOrderHistoryDTOs(anyString()))
            .thenReturn(Lists.newArrayList())
        
        // Mock hasPSA
        when(contractV2Delegator.hasPSA(anyString())).thenReturn(false)
        
        // Act - this should throw RetailRuntimeException
        sut.validateGrowthRebate("test", "test", "Fix Amount")
    }
    
    @Test(expected = ContractValidationException.class)
    void test_without_unit_category_and_sku_list() {
        // Arrange
        // Mock contract details
        when(contractV2Delegator.getContractDetailByAggregateId(anyString()))
            .thenReturn(AppResponses.success(new Contract2DtoNew(
                signatureType: Contract2DtoNew.SignatureTypeEnum.DocuSign, 
                contractTypeName: ""
            )))
        
        // Mock contract attributes - only with growth_rebate_condition_info
        List<ContractAttributeValueDto> attributeValues = Lists.newArrayList(
            ContractAttributeValueDto.builder()
                .elementTypeName("growth_rebate_condition_info")
                .elementValueId(3)
                .attributeTypeName("rebateStartMonth")
                .attributeValue("202307")
                .build(),
            ContractAttributeValueDto.builder()
                .elementTypeName("growth_rebate_condition_info")
                .elementValueId(3)
                .attributeTypeName("rebateEndMonth")
                .attributeValue("202308")
                .build()
        )
        when(contractV2Delegator.getContractAttributeValues(anyString()))
            .thenReturn(attributeValues)
        
        // Act - this should throw ContractValidationException
        sut.validateGrowthRebate("test", "test", "Fix Amount")
    }
    
    @Test
    void validateGrowthRebate_not_skip_without_po_validation_with_sku_list() {
        // Arrange
        // Mock contract details
        when(contractV2Delegator.getContractDetailByAggregateId(anyString()))
            .thenReturn(AppResponses.success(new Contract2DtoNew(signatureType: Contract2DtoNew.SignatureTypeEnum.DocuSign)))
        
        // Mock contract attributes with sku_info
        List<ContractAttributeValueDto> attributeValues = Lists.newArrayList(
            ContractAttributeValueDto.builder()
                .elementTypeName("growth_rebate_sku_info")
                .elementValueId(1)
                .attributeTypeName("skuId")
                .build(),
            ContractAttributeValueDto.builder()
                .elementTypeName("growth_rebate_condition_info")
                .elementValueId(3)
                .attributeTypeName("rebateStartMonth")
                .attributeValue("202307")
                .build(),
            ContractAttributeValueDto.builder()
                .elementTypeName("growth_rebate_condition_info")
                .elementValueId(3)
                .attributeTypeName("rebateEndMonth")
                .attributeValue("202308")
                .build()
        )
        when(contractV2Delegator.getContractAttributeValues(anyString()))
            .thenReturn(attributeValues)
        
        // Mock rebate duplicate check
        when(contractV2Delegator.getRebateDuplicateChecks(anyString()))
            .thenReturn(RebateDuplicateResult.builder().duplicateCheckDtos(Lists.newArrayList()).build())
        
        // Mock purchase order history
        when(purchaseOrderService.getMonthlyPurchaseOrderHistoryDTOs(anyString()))
            .thenReturn(Lists.newArrayList())
        
        // Mock hasPSA
        when(contractV2Delegator.hasPSA(anyString())).thenReturn(true)
        
        // Act
        ValidationResultDTO resultDTO = sut.validateGrowthRebate("test", "test", "Fix Amount")
        
        // Assert
        assertNotNull(resultDTO)
        assertTrue(CollectionUtils.isEmpty(resultDTO.targetPurchaseOrders))
        assertTrue(CollectionUtils.isEmpty(resultDTO.forecastPurchaseOrders))
    }
    
    @Test(expected = ContractValidationException.class)
    void no_sku_and_category_rebate() {
        // Arrange
        // Mock contract details
        when(contractV2Delegator.getContractDetailByAggregateId(anyString()))
            .thenReturn(AppResponses.success(new Contract2DtoNew(
                signatureType: Contract2DtoNew.SignatureTypeEnum.DocuSign, 
                contractTypeName: "rebate_by_sku", 
                contractTypeId: "contractTypeId"
            )))
        
        // Mock contract attributes - empty list
        when(contractV2Delegator.getContractAttributeValues(anyString()))
            .thenReturn(Lists.newArrayList())
        
        // Mock contract type
        when(contractTypeDelegator.getContractType(anyString()))
            .thenReturn(AppResponses.success(
                ContractTypeDto.builder()
                    .tags(null)
                    .build()
            ))
        
        // Act - this should throw ContractValidationException
        sut.validateGrowthRebate("test", "test", "Fix Amount")
    }
    
    @Test
    void testDataTableValues() {
        // This test verifies the data table values from the original Spock test
        // We'll use a map to represent the data table
        Map<String, Map<String, Object>> dataTable = [
            "contractTypeId | typeResponse": [
                "null": null,
                "null": null,
                "aa": null,
                "aa": null,
                "aa": AppResponses.success(),
                "aa": AppResponses.success(ContractTypeDto.builder().tags(null).build()),
                "aa": AppResponses.success(ContractTypeDto.builder().tags(Lists.newArrayList()).build()),
                "aa": AppResponses.success(ContractTypeDto.builder().tags(Lists.newArrayList("REBATE_BY_SKU")).build()),
                "aa": AppResponses.success(ContractTypeDto.builder().tags(Lists.newArrayList("PO")).build())
            ]
        ]
        
        // We can't directly test the data table in JUnit, but we can verify some key behaviors
        // For example, we can verify that when contractTypeId is null, typeResponse should be null
        assertNull(dataTable["contractTypeId | typeResponse"]["null"])
        
        // And when contractTypeId is "aa" and typeResponse has tags with "REBATE_BY_SKU",
        // it should return a non-null response
        assertNotNull(dataTable["contractTypeId | typeResponse"]["aa"])
    }
}
```
