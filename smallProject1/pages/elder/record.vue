<template>
  <view style="padding: 24px;">
    <view style="font-size: 20px; font-weight: 600; margin-bottom: 16px;">
      老人录音
    </view>

    <!-- 按住录音：touchstart；松开停止：touchend -->
    <button
      type="primary"
      :disabled="uploading"
      @touchstart="startRecord"
      @touchend="stopRecord"
      @touchcancel="stopRecord"
      style="height: 72px; font-size: 20px;"
    >
      {{ recording ? "松开结束并上传" : "按住说话" }}
    </button>

    <view style="margin-top: 16px; font-size: 16px;">
      状态：{{ status }}
    </view>

    <view v-if="lastTempFilePath" style="margin-top: 8px; font-size: 12px; color: #666;">
      文件：{{ lastTempFilePath }}
    </view>

    <view v-if="result" style="margin-top: 12px; font-size: 14px;">
      返回：{{ result }}
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from "vue";

const API_BASE = "http://localhost:8000"; // ⚠️ 真机不能用 localhost，后面改成你的服务器地址
const elderId = 123; // MVP 先写死

const recording = ref(false);
const uploading = ref(false);
const status = ref("idle");
const result = ref("");
const lastTempFilePath = ref("");

let recorder = null;

onMounted(() => {
  recorder = uni.getRecorderManager();

  recorder.onStart(() => {
    status.value = "录音中...";
  });

  recorder.onStop((res) => {
    // ✅ 这里产生“音频文件”：系统录音后生成临时文件路径
    const tempPath = res.tempFilePath;
    lastTempFilePath.value = tempPath;
    status.value = "录音结束，准备上传...";

    uploadAudio(tempPath);
  });

  recorder.onError((err) => {
    recording.value = false;
    status.value = "录音失败：" + JSON.stringify(err);
  });
});

function startRecord() {
  if (uploading.value) return;

  status.value = "开始录音...";
  result.value = "";
  lastTempFilePath.value = "";

  // 开始录音（会触发权限弹窗）
  recorder.start({
    duration: 60 * 1000,
    sampleRate: 16000,
    numberOfChannels: 1,
    encodeBitRate: 32000,
    format: "wav", // 确保后端允许 wav
  });

  recording.value = true;
}

function stopRecord() {
  if (!recording.value) return;
  status.value = "停止录音...";
  recording.value = false;

  // 触发 onStop 回调，拿到 tempFilePath
  recorder.stop();
}

function uploadAudio(filePath) {
  uploading.value = true;
  status.value = "上传中...";

  uni.uploadFile({
    url: `${API_BASE}/listen/upload`,
    filePath,
    name: "audio_file", // ✅ 必须和后端一致
    formData: {
      elder_id: String(elderId),
    },
    success: (res) => {
      uploading.value = false;

      // res.data 是字符串
      try {
        const data = JSON.parse(res.data);
        result.value = JSON.stringify(data);
        status.value = "上传成功，record_id=" + data.record_id;
      } catch (e) {
        result.value = res.data;
        status.value = "上传成功（但返回不是 JSON）";
      }
    },
    fail: (err) => {
      uploading.value = false;
      status.value = "上传失败：" + JSON.stringify(err);
    },
  });
}
</script>
