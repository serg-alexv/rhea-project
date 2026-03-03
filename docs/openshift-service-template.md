# Create Rhea Service on OpenShift (Knative)

Use this template when you want to host a Rhea export/microservice inside the OpenShift sandbox and expose it to the Rhea tasklist.

```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: rhea-biomolecula-export
  namespace: mrfeynman-dev
spec:
  template:
    spec:
      containers:
        - image: <your registry>/rhea-biomolecula-export:latest
          env:
            - name: TASK_DB_URI
              valueFrom:
                secretKeyRef:
                  name: rhea-secrets
                  key: TASK_DB_URI
            - name: BIORENDERER_TEMPLATE_KEY
              valueFrom:
                secretKeyRef:
                  name: rhea-secrets
                  key: BIORENDERER_TEMPLATE_KEY
          ports:
            - containerPort: 8080
```

Steps:
1. Replace `<your registry>` with the image you publish (e.g., `ghcr.io/timelabs-npo/rhea-export`).
2. Create Kubernetes Secret `rhea-secrets` with `TASK_DB_URI` and `BIORENDERER_TEMPLATE_KEY` (use `oc create secret generic`).
3. Click **Create** in the OpenShift dialog or apply via `oc apply -f`. This service becomes the `rhea-biomolecula-export` endpoint.
4. Use `oc expose svc/rhea-biomolecula-export` to create a Route, then capture the URL and store it in `docs/playui-swarm-plan.md` and `docs/orchestrate-inspired.md`.
5. Once the route is ready, restart the Rhea swarm so exports hit that service and publish results.

Need me to create matching Relay/task for the swarm to build the image, push to registry, and deploy the service automatically?"EOF