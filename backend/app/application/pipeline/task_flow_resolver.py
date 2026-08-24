from app.domain.enums.task_type import (
    TaskType,
)


class TaskFlowResolver:

    _FLOW = {

        TaskType.DOWNLOAD: [
            TaskType.EXTRACT,
        ],

        TaskType.EXTRACT: [
            TaskType.CHUNK,
        ],

        TaskType.CHUNK: [
            TaskType.CLASSIFY,
            TaskType.EMBED,
        ],

        TaskType.CLASSIFY: [],

        TaskType.EMBED: [],

        TaskType.INDEX: [],
    }

    def get_next_task_types(
        self,
        current_task_type: TaskType,
    ) -> list[TaskType]:

        return self._FLOW.get(
            current_task_type,
            [],
        )