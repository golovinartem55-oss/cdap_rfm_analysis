# Лабораторная работа №3 — Вариант 11
## Развертывание приложения RFM Analysis в Kubernetes

**Студент:** Головин Артём  
**Группа:** БД251-м
**Вариант:** 11

---

## 1. Описание архитектуры

| Компонент | В Docker Compose | В Kubernetes |
|-----------|-----------------|--------------|
| MongoDB | Service + named volume | StatefulSet + PVC + Service ClusterIP |
| Loader | depends_on | Job |
| App | healthcheck | Deployment + InitContainer + Probes + Service NodePort |
| Конфигурация | .env | ConfigMap + Secret |
| Registry | локальный | Secret docker-registry |

**Особенности варианта 11:**  
Использован Secret типа docker-registry для симуляции пулла из закрытого реестра.

---

## 2. Листинги манифестов

Все манифесты находятся в директории `lab_03/manifests/` репозитория.

---

## 3. Скриншоты

### 3.1. Статус Minikube
![minikube status](screenshots/01_minikube_status.png)

### 3.2. Секрет docker-registry
![docker-registry secret](screenshots/02_registry_secret.png)

### 3.3. Загруженные образы
![loaded images](screenshots/03_loaded_images.png)

### 3.4. kubectl get all
![kubectl get all](screenshots/04_kubectl_get_all.png)

### 3.5. Логи Job
![job logs](screenshots/05_job_logs.png)

### 3.6. Health check
![health check](screenshots/06_health_check.png)

### 3.7. ImagePullSecrets в поде
![image pull secrets](screenshots/07_image_pull_secrets.png)

### 3.8. PVC
![pvc](screenshots/08_pvc.png)

### 3.9. Персистентность данных
![persistence](screenshots/09_persistence.png)

---

## 4. Вывод

✅ Манифесты корректно описаны  
✅ Конфигурация вынесена в ConfigMap и Secret  
✅ Данные сохраняются в PVC  
✅ Настроены Probes и InitContainer  
✅ Реализована специфика варианта 11 — Secret docker-registry
