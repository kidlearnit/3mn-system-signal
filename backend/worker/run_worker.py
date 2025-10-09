from base_worker import BaseRQWorker


class DefaultWorker(BaseRQWorker):
    def get_listen_queues(self) -> list[str]:
        return ['default', 'priority']


if __name__ == '__main__':
    DefaultWorker().run(with_scheduler=True)
