from label_studio_sdk import Client
from label_studio_sdk.client import ClientCredentials

from env import LABEL_STUDIO_HOST, LABEL_STUDIO_USER_TOKEN, LABEL_STUDIO_SEGMENT_MATCH_PROJECT_ID, \
    LABEL_STUDIO_SEGMENT_CLASSIFY_PROJECT_ID

LabelStudioClient = Client(
    url=LABEL_STUDIO_HOST,
    credentials=ClientCredentials(api_key=LABEL_STUDIO_USER_TOKEN),
)

LSSegmentMatchProject = LabelStudioClient.get_project(int(LABEL_STUDIO_SEGMENT_MATCH_PROJECT_ID))
matching_label_config = """
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
      <TimeSeries name="ts" value="$csv" valueType="url" timeColumn="index">
        <Channel column="ax3_bandpass"/>
      </TimeSeries>
    </View>
  </View>
</View>
"""
if LSSegmentMatchProject.label_config != matching_label_config:
    LSSegmentMatchProject.set_params(label_config=matching_label_config)
LSSegmentClassifyProject = LabelStudioClient.get_project(int(LABEL_STUDIO_SEGMENT_CLASSIFY_PROJECT_ID))
classify_label_config = """
<View>
  <View style="width: 100%">
    <HyperText name="video" value="$video" inline="true"/>
    <TimeSeries name="ts" value="$csv" valueType="url" timeColumn="index">
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
</View>
"""
if LSSegmentClassifyProject.label_config != classify_label_config:
    LSSegmentClassifyProject.set_params(label_config=classify_label_config)
