pipeline {
    agent any

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Secret Scan') {
            steps {
                script {

                    sh '''
                    echo "Running Gitleaks scan..."
                    
                    set +e
                    gitleaks git \
                      --log-opts="--all" \
                      --report-format=json \
                      --report-path=report.json \
                      --redact

                    EXIT_CODE=$?
                    set -e

                    echo "========== GITLEAKS REPORT =========="
                    cat report.json || echo "No report generated"
                    echo "====================================="

                    exit $EXIT_CODE
                    '''
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'report.json', allowEmptyArchive: true
        }
    }
}
