
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
 package com.coupang.retail.contract_admin.app.web.contract.supplier

import com.coupang.apigateway.services.vendor.model.VendorDto
import com.coupang.apigateway.services.vendor.model.VendorPageOfVendorDto
import com.coupang.retail.contract_admin.app.delegate.supplier.SupplierDelegator
import com.coupang.retail.contract_admin.app.service.supplier.UnitCategoryService
import com.coupang.retail.contract_admin.app.service.vendor.VendorEmployeeService
import com.coupang.retail.contract_admin.app.shared.AppResponse
import com.coupang.retail.contract_admin.app.shared.PageNavigator
import com.coupang.retail.contract_admin.app.shared.RsProjectConfig
import com.coupang.retail.contract_admin.app.shared.utils.SecurityUtils
import com.coupang.retail.contract_admin.app.web.contract.facade.SirtMaskingFacade
import com.coupang.retail.contract_admin.app.web.contract.supplier.dto.VendorFindResponseDto
import com.coupang.retail.contract_admin.app.web.contract.supplier.generator.VendorFindResponseDtoGenerator
import org.apache.commons.collections4.CollectionUtils
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
public class ContractSupplierControllerTest {
    
    private static final String TEST_USER_ID = "test_userId"
    private static final String SUPPLIER_ID = "A00123456"
    private static final String SUPPLIER_NAME = "a"
    
    @Mock
    RsProjectConfig config;
    
    @Mock
    SirtMaskingFacade sirtMaskingFacade;
    
    @Mock
    UnitCategoryService unitCategoryService;
    
    @Mock
    VendorEmployeeService vendorEmployeeService;
    
    @Mock
    SupplierDelegator supplierDelegator;
    
    @Mock
    VendorFindResponseDtoGenerator vendorFindResponseDtoGenerator;
    
    @InjectMocks
    ContractSupplierController stub;
    
    // Test data
    VendorDto vendorDto;
    VendorPageOfVendorDto vendorPageDto;
    
    @Before
    public void setup() {
        MockitoAnnotations.openMocks(this);
        
        // Mock SecurityUtils static method
        try (MockedStatic<SecurityUtils> mockedSecurityUtils = mockStatic(SecurityUtils.class)) {
            mockedSecurityUtils.when(() -> SecurityUtils.getCurrentLoginId()).thenReturn(TEST_USER_ID);
        }
        
        // Initialize test data
        vendorDto = VendorDto.builder()
            .vendorId(SUPPLIER_ID)
            .vendorName("test_vendorName")
            .businessNumber("test_businessNumber")
            .repPersonName("test_repPersonName")
            .repMobileNum("test_repMobileNum")
            .repPhoneNum("test_repPhoneNum")
            .repEmail("test_repEmail")
            .repZip("test_repZip")
            .repAddr1("test_repAddr1")
            .repAddr2("test_repAddr2")
            .build();
            
        List<VendorDto> vendorDtos = [vendorDto];
        
        vendorPageDto = VendorPageOfVendorDto.builder()
            .page(1)
            .sizePerPage(10)
            .totalElements(1)
            .totalPages(1)
            .content(vendorDtos)
            .build();
    }
    
    @Test
    public void testGetVendorList_HasPermission() {
        // Arrange
        String supplierName = SUPPLIER_NAME;
        Integer currentPage = 1;
        Integer countPerPage = 10;
        
        // Mock vendor employee service
        when(vendorEmployeeService.getVendorListByName(supplierName, currentPage, countPerPage))
            .thenReturn(vendorPageDto);
            
        // Mock SIRT permission check
        when(sirtMaskingFacade.findAccessibleVendorIds(TEST_USER_ID, [SUPPLIER_ID]))
            .thenReturn([SUPPLIER_ID] as Set);
            
        // Mock vendor find response generator
        VendorFindResponseDto responseDto = VendorFindResponseDto.builder()
            .vendorId(SUPPLIER_ID)
            .haveViewPermission(true)
            .vendorName("test_vendorName")
            .businessNumber("test_businessNumber")
            .repPersonName("test_repPersonName")
            .repMobileNum("test_repMobileNum")
            .repPhoneNum("test_repPhoneNum")
            .repEmail("test_repEmail")
            .repZip("test_repZip")
            .repAddr1("test_repAddr1")
            .repAddr2("test_repAddr2")
            .build();
            
        when(vendorFindResponseDtoGenerator.generateList(anyList(), anySet()))
            .thenReturn([responseDto]);
            
        // Act
        AppResponse<PageNavigator<VendorFindResponseDto>> actual = 
            stub.getVendorList(supplierName, currentPage, countPerPage);
            
        // Assert
        assertTrue(CollectionUtils.isEmpty(actual.getErrors()));
        assertEquals(1, actual.getData().getCurrentPage());
        assertEquals(1, actual.getData().getTotalPages());
        assertEquals(10, actual.getData().getElementCountPerPage());
        assertEquals(1, actual.getData().getTotalElements());
        assertEquals(1, actual.getData().getContents().size());
        
        VendorFindResponseDto vendorFindResponseDto = actual.getData().getContents().iterator().next();
        assertEquals(SUPPLIER_ID, vendorFindResponseDto.getVendorId());
        assertTrue(vendorFindResponseDto.isHaveViewPermission());
        assertEquals("test_vendorName", vendorFindResponseDto.getVendorName());
        assertEquals("test_businessNumber", vendorFindResponseDto.getBusinessNumber());
        assertEquals("test_repPersonName", vendorFindResponseDto.getRepPersonName());
        assertEquals("test_repMobileNum", vendorFindResponseDto.getRepMobileNum());
        assertEquals("test_repPhoneNum", vendorFindResponseDto.getRepPhoneNum());
        assertEquals("test_repEmail", vendorFindResponseDto.getRepEmail());
        assertEquals("test_repZip", vendorFindResponseDto.getRepZip());
        assertEquals("test_repAddr1", vendorFindResponseDto.getRepAddr1());
        assertEquals("test_repAddr2", vendorFindResponseDto.getRepAddr2());
    }
    
    @Test
    public void testGetVendorList_DoesNotHavePermission() {
        // Arrange
        String supplierName = SUPPLIER_NAME;
        Integer currentPage = 1;
        Integer countPerPage = 10;
        
        // Mock vendor employee service
        when(vendorEmployeeService.getVendorListByName(supplierName, currentPage, countPerPage))
            .thenReturn(vendorPageDto);
            
        // Mock SIRT permission check - no permission
        when(sirtMaskingFacade.findAccessibleVendorIds(TEST_USER_ID, [SUPPLIER_ID]))
            .thenReturn([] as Set);
            
        // Mock vendor find response generator
        VendorFindResponseDto responseDto = VendorFindResponseDto.builder()
            .vendorId(SUPPLIER_ID)
            .haveViewPermission(false)
            .vendorName("test_vendorName")
            .businessNumber("******")
            .repPersonName("******")
            .repMobileNum("******")
            .repPhoneNum("******")
            .repEmail("******")
            .repZip("******")
            .repAddr1("******")
            .repAddr2("******")
            .build();
            
        when(vendorFindResponseDtoGenerator.generateList(anyList(), anySet()))
            .thenReturn([responseDto]);
            
        // Act
        AppResponse<PageNavigator<VendorFindResponseDto>> actual = 
            stub.getVendorList(supplierName, currentPage, countPerPage);
            
        // Assert
        assertTrue(CollectionUtils.isEmpty(actual.getErrors()));
        assertEquals(1, actual.getData().getCurrentPage());
        assertEquals(1, actual.getData().getTotalPages());
        assertEquals(10, actual.getData().getElementCountPerPage());
        assertEquals(1, actual.getData().getTotalElements());
        assertEquals(1, actual.getData().getContents().size());
        
        VendorFindResponseDto vendorFindResponseDto = actual.getData().getContents().iterator().next();
        assertEquals(SUPPLIER_ID, vendorFindResponseDto.getVendorId());
        assertFalse(vendorFindResponseDto.isHaveViewPermission());
        assertEquals("test_vendorName", vendorFindResponseDto.getVendorName());
        assertEquals("******", vendorFindResponseDto.getBusinessNumber());
        assertEquals("******", vendorFindResponseDto.getRepPersonName());
        assertEquals("******", vendorFindResponseDto.getRepMobileNum());
        assertEquals("******", vendorFindResponseDto.getRepPhoneNum());
        assertEquals("******", vendorFindResponseDto.getRepEmail());
        assertEquals("******", vendorFindResponseDto.getRepZip());
        assertEquals("******", vendorFindResponseDto.getRepAddr1());
        assertEquals("******", vendorFindResponseDto.getRepAddr2());
    }
    
    @Test
    public void testGetVendorByVendorId_HasPermission() {
        // Arrange
        String supplierId = SUPPLIER_ID;
        
        // Mock vendor employee service
        when(vendorEmployeeService.getByVendorId(supplierId))
            .thenReturn(vendorDto);
            
        // Mock SIRT permission check
        when(sirtMaskingFacade.checkPermission(TEST_USER_ID, SUPPLIER_ID))
            .thenReturn(true);
            
        // Mock vendor find response generator
        VendorFindResponseDto responseDto = VendorFindResponseDto.builder()
            .vendorId(SUPPLIER_ID)
            .haveViewPermission(true)
            .vendorName("test_vendorName")
            .businessNumber("test_businessNumber")
            .repPersonName("test_repPersonName")
            .repMobileNum("test_repMobileNum")
            .repPhoneNum("test_repPhoneNum")
            .repEmail("test_repEmail")
            .repZip("test_repZip")
            .repAddr1("test_repAddr1")
            .repAddr2("test_repAddr2")
            .build();
            
        when(vendorFindResponseDtoGenerator.generate(any(VendorDto.class), eq(true)))
            .thenReturn(responseDto);
            
        // Act
        AppResponse<VendorFindResponseDto> actual = stub.getVendorByVendorId(supplierId);
            
        // Assert
        assertTrue(CollectionUtils.isEmpty(actual.getErrors()));
        assertEquals(SUPPLIER_ID, actual.getData().getVendorId());
        assertTrue(actual.getData().isHaveViewPermission());
        assertEquals("test_vendorName", actual.getData().getVendorName());
        assertEquals("test_businessNumber", actual.getData().getBusinessNumber());
        assertEquals("test_repPersonName", actual.getData().getRepPersonName());
        assertEquals("test_repMobileNum", actual.getData().getRepMobileNum());
        assertEquals("test_repPhoneNum", actual.getData().getRepPhoneNum());
        assertEquals("test_repEmail", actual.getData().getRepEmail());
        assertEquals("test_repZip", actual.getData().getRepZip());
        assertEquals("test_repAddr1", actual.getData().getRepAddr1());
        assertEquals("test_repAddr2", actual.getData().getRepAddr2());
    }
    
    @Test
    public void testGetVendorByVendorId_DoesNotHavePermission() {
        // Arrange
        String supplierId = SUPPLIER_ID;
        
        // Mock vendor employee service
        when(vendorEmployeeService.getByVendorId(supplierId))
            .thenReturn(vendorDto);
            
        // Mock SIRT permission check - no permission
        when(sirtMaskingFacade.checkPermission(TEST_USER_ID, SUPPLIER_ID))
            .thenReturn(false);
            
        // Mock vendor find response generator
        VendorFindResponseDto responseDto = VendorFindResponseDto.builder()
            .vendorId(SUPPLIER_ID)
            .haveViewPermission(false)
            .vendorName("test_vendorName")
            .businessNumber("******")
            .repPersonName("******")
            .repMobileNum("******")
            .repPhoneNum("******")
            .repEmail("******")
            .repZip("******")
            .repAddr1("******")
            .repAddr2("******")
            .build();
            
        when(vendorFindResponseDtoGenerator.generate(any(VendorDto.class), eq(false)))
            .thenReturn(responseDto);
            
        // Act
        AppResponse<VendorFindResponseDto> actual = stub.getVendorByVendorId(supplierId);
            
        // Assert
        assertTrue(CollectionUtils.isEmpty(actual.getErrors()));
        assertEquals(SUPPLIER_ID, actual.getData().getVendorId());
        assertFalse(actual.getData().isHaveViewPermission());
        assertEquals("test_vendorName", actual.getData().getVendorName());
        assertEquals("******", actual.getData().getBusinessNumber());
        assertEquals("******", actual.getData().getRepPersonName());
        assertEquals("******", actual.getData().getRepMobileNum());
        assertEquals("******", actual.getData().getRepPhoneNum());
        assertEquals("******", actual.getData().getRepEmail());
        assertEquals("******", actual.getData().getRepZip());
        assertEquals("******", actual.getData().getRepAddr1());
        assertEquals("******", actual.getData().getRepAddr2());
    }
    
    @Test
    public void testSearchSkuInfo() {
        // Arrange
        when(supplierDelegator.getSku(anyString())).thenReturn(new AppResponse());
        
        // Act
        AppResponse result = stub.searchSkuInfo("", 1);
        
        // Assert
        assertNotNull(result);
    }
    
    @Test
    public void testGetSecondUnitToKanMapping() {
        // Arrange
        when(unitCategoryService.getSecondUnitToKanMapping()).thenReturn(new AppResponse());
        
        // Act
        AppResponse result = stub.getSecondUnitToKanMapping();
        
        // Assert
        assertNotNull(result);
    }
}
```
