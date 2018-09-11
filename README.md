# service-ingestion-initiation
[ ![Codeship Status for advisorconnect/service-ingest-initiation](https://app.codeship.com/projects/7489e4e0-3d94-0135-0993-02707c28cc3a/status?branch=production)](https://app.codeship.com/projects/229236)

Pulls down Rabbit messages for contact ingest iniation, pulls down associated file, the underlying contacts into batches of 5 and puts them back up on Rabbit.

## CI incrementing places
### CI is currently disabled
- ./build.sh
- ./k8s/production/01-deployment.yml
- ./codeship-steps.yml
- ./scripts/deploy_to_k8s.sh


# Kubernetes 
###### (*REQUIREMENT*: working install of kubectl, functioning namespace with elasticsearch running as service with name = elasticsearch, working gcloud installation with alpha image registry functionality)
```bash
bash build.sh
kubectl create -f ./k8s/<ENVIRONMENT>/00-service.yaml
kubectl create -f ./k8s/<ENVIRONMENT>/01-deployment.yaml
```


# Local
### Install


```bash
$ virtualenv venv -p python3
$ . venv/bin/activate
$ pip install -r requirements.txt
```

### Run (dev)

```bash
kubectl port-forward $(kc get pod --namespace=infrastructure | grep els-client | head -n1 | awk '{print $1}') 9200 --namespace=infrastructure
source .dev.env
python listener.py
```
