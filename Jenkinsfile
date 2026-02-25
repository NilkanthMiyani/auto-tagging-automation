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

                    if [ "$EXIT_CODE" -ne 0 ]; then
                      echo "⚠️Secrets detected, but not failing the build."
                    else
                      echo "No secrets found."
                    fi

                    exit 0
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
