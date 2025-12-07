from celery import Celery, Task

def celery_init_app(app):
    class FlaskTask(Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(
        app.name,
        task_cls=FlaskTask,
        broker=app.config['CELERY']['broker_url'],
        backend=app.config['CELERY']['result_backend']
    )
    celery_app.set_default()
    celery_app.conf.update(app.config.get('CELERY'))
    app.extensions['celery'] = celery_app
    return celery_app