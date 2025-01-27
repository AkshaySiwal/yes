/**
 * Common Functions to be used for automated run pipelines
 */

def massDeployCloudManagementRole(deployment_dir) {
    // List accounts directories under cloud-management-role
    def envList = []
    def resourceList = []
    
    def output_dir = sh(script: "ls -l ${WORKSPACE}/${deployment_dir} | grep ^d | awk '{print \\$9}'", returnStdout: true)
    envList = output_dir.tokenize('\n').collect() { 
        it 
    }
    
    for (dir in envList) {
        print("Account directory is : $dir")
        resourceList.add("$deployment_dir/$dir")
    }
    
    println("Available Accounts: \n" + resourceList)
    return resourceList
}

def parallelBuild(buildableResourcePaths, action, assumeRoleArn) {
    def batchArray = buildableResourcePaths.collate(10)
    batchArray.each { List batch ->
        def parallelStages = [:]
        
        try {
            if (buildableResourcePaths.isEmpty()) {
                println("No accounts detected to process")
            } else {
                batch.each {
                    path ->
                        def accountID = sh(script: "echo $path | tr '/' '\\n' | tail -1", returnStdout: true)
                        println("Account ID is : ${accountID}")
                        parallelStages[accountID] = {
                            stage(accountID) {
                                println("Listing S3 buckets for account: ${accountID}")
                                runAwsCommand(action, assumeRoleArn)
                            }
                        }
                }
                parallel parallelStages
            }
        } catch (err) {
            println("Intermediate Failure: $err")
            throw err
        }
    }
}

def runAwsCommand(action, AssumeRoleArn) {
    def runScript = sh(script: "${WORKSPACE}/build/scripts/aws_runner.sh " +
        "--action ${action} " +
        "--assume_arn ${AssumeRoleArn}", returnStdout: true)
    println("S3 Buckets:\n${runScript}")
}

return this
