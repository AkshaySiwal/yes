#!/usr/bin/env groovy
@Library('devops-dsl')_

def build
def resourcesToBuild = []
def notifyChannel = "aws-s3-list-notification"
def slackMessage = """
Pipeline    : AWS S3 Bucket List Pipeline
Job         : ${env.JOB_NAME} [${env.BUILD_NUMBER}]
ConsoleOutput: <${env.BUILD_URL}|${env.JOB_NAME} [#${env.BUILD_NUMBER}]>
"""

pipeline {
    agent {
        docker {
            alwaysPull true
            image "aws-cli:latest"  // Change to appropriate AWS CLI image
            label "aws-cli"
            args "--net host"
        }
    }

    options {
        disableResume()
        disableConcurrentBuilds()
        timestamps()
        ansiColor('xterm')
    }

    stages {
        stage('Build') {
            steps {
                script {
                    println("Loading common build functions")
                    build = load "$WORKSPACE/build/pipelines/build_functions.groovy"
                }
            }
        }

        stage('Fetch Account Directories') {
            steps {
                script {
                    deployment_dir = "src/accounts"  // Directory containing account information
                    resourcesToBuild = build.massDeployCloudManagementRole(deployment_dir)
                }
            }
        }

        stage("List S3 Buckets") {
            steps {
                script {
                    assume_arn = "arn:aws:iam::623964595746:role/cross-account-role"  // Your cross-account role
                    build.parallelBuild(resourcesToBuild, "list", assume_arn)
                }
            }
        }
    }

    post {
        always {
            echo 'Cleaning up workspace'
            cleanWs()
        }
        success {
            slackNotify("${notifyChannel}", "*SUCCESS*\n${slackMessage}")
        }
        failure {
            slackNotify("${notifyChannel}", "*FAILURE*\n${slackMessage}")
        }
    }
}
