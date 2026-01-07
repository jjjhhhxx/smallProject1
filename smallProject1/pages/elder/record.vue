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

// ⚠️ 真机/上线必须换成 https 域名，并配置小程序合法域名
const API_BASE = "http://localhost:8000";

// 录音与页面状态
const recording = ref(false);
const uploading = ref(false);
const status = ref("");

// ✅ 关键：token（用它来识别是哪个老人）
const token = ref("");

let recorder = null;

onMounted(async () => {
  recorder = uni.getRecorderManager();

  recorder.onStop((res) => {
    uploadAudio(res.tempFilePath);
  });

  recorder.onError(() => {
    recording.value = false;
    uploading.value = false;
    status.value = "录音失败";
  });

  // ✅ 启动时先确保已登录拿到 token
  await ensureLoginToken();
});

/** 确保本地有 token；没有就走 uni.login -> 后端换 token */
async function ensureLoginToken() {
  // 1) 先读本地缓存
  const cached = uni.getStorageSync("elder_token");
  if (cached) {
    token.value = cached;
    return true;
  }

  // 2) 没有缓存：走微信登录
  try {
    const loginRes = await new Promise((resolve, reject) => {
      uni.login({
        provider: "weixin",
        success: resolve,
        fail: reject,
      });
    });

    if (!loginRes.code) throw new Error("no code");

    // 3) 拿 code 去后端换 token
    const resp = await new Promise((resolve, reject) => {
      uni.request({
        url: `${API_BASE}/auth/wx/login`,
        method: "POST",
        data: {
          code: loginRes.code,
          role: "elder", // 可选：让后端区分老人/子女
        },
        success: resolve,
        fail: reject,
      });
    });

    const data = resp.data || {};
    if (!data.token) throw new Error("no token in response");

    token.value = data.token;
    uni.setStorageSync("elder_token", token.value);

    return true;
  } catch (e) {
    // 登录失败：后续上传也会失败
    status.value = "录音失败";
    return false;
  }
}

function startRecord() {
  if (uploading.value) return;

  status.value = "";
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

async function uploadAudio(filePath) {
  uploading.value = true;

  // ✅ 上传前再兜底一次：确保 token 存在（防止缓存被清）
  const ok = await ensureLoginToken();
  if (!ok) {
    uploading.value = false;
    status.value = "录音失败";
    return;
  }

  uni.uploadFile({
    url: `${API_BASE}/listen/upload`,
    filePath,
    name: "audio_file",

    // ✅ 关键：带 token 给后端识别老人身份
    header: {
      Authorization: `Bearer ${token.value}`,
    },

    // ✅ 方案A：不再传 elder_id（避免伪造）
    // formData: {},

    success: (res) => {
      uploading.value = false;
      try {
        const data = JSON.parse(res.data || "{}");
        // 你原来的判定逻辑保留
        status.value = data && (data.record_id || data.ok === true) ? "录音完成" : "录音失败";
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
