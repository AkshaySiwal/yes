pipeline {
    agent any

    parameters {
        string(name: 'Slave_Account', defaultValue: '', description: 'Enter the Slave_Account value (cannot be empty)')
    }

    stages {
        stage('Validate Input') {
            steps {
                script {
                    if (params.Slave_Account == null || params.Slave_Account.trim() == '') {
                        error("Error: Slave_Account parameter is empty. Please provide a valid value.")
                    }
                }
                echo "Slave_Account is set to: ${params.Slave_Account}"
            }
        }

        stage('Run Python Script') {
            steps {
                echo "Running Python script: main.py"
                sh """
                python3 main.py
                """
            }
        }

        stage('Archive Artefacts') {
            steps {
                echo "Archiving artefacts starting with 'total_' and ending with '.csv'"
                archiveArtifacts artifacts: 'total_*.csv', allowEmptyArchive: true
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Please check the logs.'
        }
    }
}
