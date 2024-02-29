pipeline {
    agent any

    parameters {
        string(name: 'DEPLOY_ENV', defaultValue: 'staging', description: 'The environment to deploy to')
    }

    environment {
        VENV = 'venv'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python Environment') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                        python3 -m venv $VENV
                        . $VENV/bin/activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        '''
                    } else {
                        bat '''
                        python -m venv %VENV%
                        %VENV%\\Scripts\\activate
                        pip install --upgrade pip
                        pip install -r requirements.txt
                        '''
                    }
                }
            }
        }

        stage('Lint and Test') {
            parallel {
                stage('Lint') {
                    steps {
                        script {
                            if (isUnix()) {
                                sh '''
                                . $VENV/bin/activate
                                pip install flake8
                                flake8 --statistics --output-file lint-report.txt
                                '''
                            } else {
                                bat '''
                                %VENV%\\Scripts\\activate
                                pip install flake8
                                flake8 --statistics --output-file lint-report.txt
                                '''
                            }
                        }
                    }
                    post {
                        always {
                            archiveArtifacts artifacts: 'lint-report.txt', fingerprint: true
                        }
                    }
                }
                stage('Unit Test') {
                    steps {
                        script {
                            if (isUnix()) {
                                sh '''
                                . $VENV/bin/activate
                                pytest --junit-xml=pytest-report.xml
                                '''
                            } else {
                                bat '''
                                %VENV%\\Scripts\\activate
                                pytest --junit-xml=pytest-report.xml
                                '''
                            }
                        }
                    }
                    post {
                        always {
                            junit 'pytest-report.xml'
                        }
                    }
                }
            }
        }

        stage('Train Model') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                        . $VENV/bin/activate
                        python3 healthcare.py
                        '''
                    } else {
                        bat '''
                        %VENV%\\Scripts\\activate
                        python healthcare.py
                        '''
                    }
                }
            }
        }

        stage('Archive Model') {
            steps {
                script {
                    if (isUnix()) {
                        sh 'mkdir -p artifacts'
                    } else {
                        bat 'if not exist artifacts mkdir artifacts'
                    }
                    sh 'cp -r model/* artifacts/'
                }
                archiveArtifacts artifacts: 'artifacts/**', fingerprint: true
            }
        }

        stage('Deploy Model') {
            when {
                allOf {
                    branch 'main'
                    expression { params.DEPLOY_ENV == 'production' }
                }
            }
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                        . $VENV/bin/activate
                        python3 deploy.py --env $DEPLOY_ENV
                        '''
                    } else {
                        bat '''
                        %VENV%\\Scripts\\activate
                        python deploy.py --env %DEPLOY_ENV%
                        '''
                    }
                }
            }
        }
    }

    post {
        success {
            echo 'Pipeline succeeded!'
        }
        failure {
            echo 'Pipeline failed!'
        }
        always {
            echo 'Cleaning up...'
            script {
                if (isUnix()) {
                    sh 'rm -rf $VENV'
                } else {
                    bat 'if exist %VENV% rmdir /s /q %VENV%'
                }
            }
        }
    }
}
