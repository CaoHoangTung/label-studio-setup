from typing import Optional

import label_studio_sdk
from label_studio_sdk import Client
from label_studio_sdk.client import ClientCredentials

from env import LABEL_STUDIO_HOST, LABEL_STUDIO_USER_TOKEN, LABEL_STUDIO_EMAIL, LABEL_STUDIO_PASSWORD

LabelStudioClient = Client(
    url=LABEL_STUDIO_HOST,
    credentials=ClientCredentials(email=LABEL_STUDIO_EMAIL, password=LABEL_STUDIO_PASSWORD),
)


def set_connect_local_import_storage(
        project: label_studio_sdk.Project,
        local_store_path: [str],
        regex_filter: Optional[str] = None,
        use_blob_urls: Optional[bool] = True,
        title: Optional[str] = '',
        description: Optional[str] = '',
):
    payload = {
        'regex_filter': regex_filter,
        'use_blob_urls': use_blob_urls,
        'path': local_store_path,
        'presign': False,
        'presign_ttl': 1,
        'title': title,
        'description': description,
        'project': project.id,
    }
    response = project.make_request(
        'POST', f'/api/storages/localfiles?project={project.id}', json=payload
    )
    return response.json()


def get_project(project_name, label_config):
    projects = LabelStudioClient.list_projects()
    projects = [project for project in projects if project.title == project_name]
    if len(projects) > 0:
        project = projects[0]
        return project

    project = LabelStudioClient.create_project(title=project_name, label_config=label_config)
    set_connect_local_import_storage(project, "/storage", title="Local storage")
    return project


MATCHING_LABEL_CONFIG = """
<View>
  <TimeSeriesLabels name="label" toName="ts">
    <Label value="Stick only"/>
    <Label value="Stick + phone call"/>
    <Label value="Stick + briefcase"/>
    <Label value="Quadripod only"/>
    <Label value="Quadripod + phone call"/>
    <Label value="Quadripod + briefcase"/>
    <Label value="Rollator"/>
    <Label value="Frame"/>
    <Label value="Running"/>
    <Label value="Static (sitting/standing/lying)"/>
    <Label value="Standing or sitting with arms active"/>
  </TimeSeriesLabels>
  <View style="display: flex;">
    <View style="width: 100%">
        <HyperText name="video" value="$video" inline="true"/>
    </View>
    <View style="width: 100%">
      <TimeSeries name="ts" value="$csv" valueType="url" timeColumn="index" fixedScale="true" overviewWidth="100%">
        <Channel column="ax3_bandpass"/>
      </TimeSeries>
    </View>
  </View>
</View>
"""

CLASSIFY_LABEL_CONFIG = """
<View>
  <View style="width: 100%">
    <HyperText name="video" value="$video" inline="true"/>
    <TimeSeries name="ts" value="$csv" valueType="url" timeColumn="index" fixedScale="true" overviewWidth="100%">
        <Channel column="ax3_bandpass"/>
      </TimeSeries>
  </View>

  <Choices name="label" toName="video">
    <Choice value="Stick only"/>
    <Choice value="Stick + phone call"/>
    <Choice value="Stick + briefcase"/>
    <Choice value="Quadripod only"/>
    <Choice value="Quadripod + phone call"/>
    <Choice value="Quadripod + briefcase"/>
    <Choice value="Rollator"/>
    <Choice value="Frame"/>
    <Choice value="Running"/>
    <Choice value="Static (sitting/standing/lying)"/>
    <Choice value="Standing or sitting with arms active"/>
  </Choices>
  <TextArea name="info"></TextArea>
</View>
"""

LSSegmentMatchProject = get_project("Segment Matching", MATCHING_LABEL_CONFIG)
LSSegmentClassifyProject = get_project("Segment Classifying", CLASSIFY_LABEL_CONFIG)
