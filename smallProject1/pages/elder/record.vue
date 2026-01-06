<template>
  <view style="padding: 24px;">
    <!-- 去掉“老人录音”标题 -->

    <button
      type="primary"
      :disabled="uploading"
      @touchstart="startRecord"
      @touchend="stopRecord"
      @touchcancel="stopRecord"
      style="
        height: 96px;
        line-height: 96px;
        font-size: 26px;
        font-weight: 700;
        border-radius: 16px;
      "
    >
      {{ recording ? "松开结束" : "按住录音" }}
    </button>

    <!-- 松开后只显示两种结果：录音完成 / 录音失败 -->
    <view v-if="status" style="margin-top: 20px; font-size: 22px; font-weight: 700; text-align: center;">
  {{ status }}
</view>

  </view>
</template>

<script setup>
import { ref, onMounted } from "vue";

const API_BASE = "http://localhost:8000";
const elderId = 123;

const recording = ref(false);
const uploading = ref(false);

// ✅ 只保留两种显示：录音完成 / 录音失败（其他阶段不显示）
const status = ref("");

let recorder = null;

onMounted(() => {
  recorder = uni.getRecorderManager();

  recorder.onStart(() => {
    // 录音中不展示任何文案（符合你“松开后才提示”的需求）
  });

  recorder.onStop((res) => {
    const tempPath = res.tempFilePath;
    // 松开后先不显示“上传中”，只等最终结果
    uploadAudio(tempPath);
  });

  recorder.onError(() => {
    recording.value = false;
    uploading.value = false;
    status.value = "录音失败";
  });
});

function startRecord() {
  if (uploading.value) return;

  status.value = "";          // 每次开始录音先清空提示
  recording.value = true;

  recorder.start({
    duration: 60 * 1000,
    sampleRate: 16000,
    numberOfChannels: 1,
    encodeBitRate: 32000,
    format: "wav",
  });
}

function stopRecord() {
  if (!recording.value) return;
  recording.value = false;
  recorder.stop();
}

function uploadAudio(filePath) {
  uploading.value = true;

  uni.uploadFile({
    url: `${API_BASE}/listen/upload`,
    filePath,
    name: "audio_file",
    formData: {
      elder_id: String(elderId),
    },
    success: (res) => {
      uploading.value = false;

      // 只要能走到 success，就认为“录音完成”（包含上传完成）
      // 如果你希望后端返回特定字段才算成功，也可以在这里再做判断
      try {
        const data = JSON.parse(res.data || "{}");
        // 可选：严格判断后端是否真的成功（比如有 record_id）
        if (data && (data.record_id || data.ok === true)) {
          status.value = "录音完成";
        } else {
          // 后端返回了非预期内容，也按失败处理（更符合“只两种信息”）
          status.value = "录音失败";
        }
      } catch (e) {
        status.value = "录音失败";
      }
    },
    fail: () => {
      uploading.value = false;
      status.value = "录音失败";
    },
  });
}
</script>
