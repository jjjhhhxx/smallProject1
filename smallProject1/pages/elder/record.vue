<template>
  <view style="padding: 24px;">
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

    <view
      v-if="status"
      style="margin-top: 20px; font-size: 22px; font-weight: 700; text-align: center;"
    >
      {{ status }}
    </view>

    <!-- ✅ 页面底部显示 elder_id -->
    <view
      v-if="elderId"
      style="margin-top: 28px; font-size: 16px; color: #666; text-align: center;"
    >
      绑定码（elder_id）：<text style="font-weight: 700; font-size: 18px; color: #333;">{{ elderId }}</text>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from "vue";

const API_BASE = "http://192.168.3.5:8000";

const recording = ref(false);
const uploading = ref(false);
const status = ref("");

const token = ref("");
const elderId = ref(""); // ✅ 新增：用于页面展示

let recorder = null;

onMounted(async () => {
  recorder = uni.getRecorderManager();

  recorder.onStop((res) => {
    console.log("[recorder.onStop]", res);
    if (!res?.tempFilePath) {
      status.value = "录音文件为空";
      uploading.value = false;
      return;
    }
    uploadAudio(res.tempFilePath);
  });

  recorder.onError(() => {
    console.error("[recorder.onError]", err);
    recording.value = false;
    uploading.value = false;
    status.value = `录音失败：${err?.errMsg || "unknown"}`;
  });

  await ensureLoginToken();
});

async function ensureLoginToken() {
  // 1) 先读本地缓存
  const cachedToken = uni.getStorageSync("elder_token");
  const cachedElderId = uni.getStorageSync("elder_id");
  if (cachedToken) token.value = cachedToken;
  if (cachedElderId) elderId.value = String(cachedElderId);

  if (cachedToken && cachedElderId) return true;

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

    // 3) 拿 code 去后端换 token（✅ role 建议用大写）
    const resp = await new Promise((resolve, reject) => {
      uni.request({
        url: `${API_BASE}/auth/wx/login`,
        method: "POST",
        data: {
          code: loginRes.code,
          role: "ELDER",
        },
        success: resolve,
        fail: reject,
      });
    });

    const data = resp.data || {};
    if (!data.token) throw new Error("no token in response");

    // ✅ 保存 token
    token.value = data.token;
    uni.setStorageSync("elder_token", token.value);

    // ✅ 保存 elder_id（后端返回 elder_id=user_id）
    if (data.elder_id) {
      elderId.value = String(data.elder_id);
      uni.setStorageSync("elder_id", elderId.value);
    } else if (data.user_id) {
      // 兜底：如果后端没返回 elder_id，就用 user_id 当 elder_id
      elderId.value = String(data.user_id);
      uni.setStorageSync("elder_id", elderId.value);
    }

    return true;
  } catch (e) {
    console.error("[ensureLoginToken.fail]", e);
    status.value = "登录失败";
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
  header: { Authorization: `Bearer ${token.value}` },
  success: (res) => {
    console.log("[upload.success]", res.statusCode, res.data);
    uploading.value = false;

    if (res.statusCode !== 200) {
      status.value = `上传失败(${res.statusCode})`;
      return;
    }

    try {
      const data = JSON.parse(res.data || "{}");
      status.value = (data.record_id || data.ok === true) ? "录音完成" : `后端返回异常：${res.data}`;
    } catch {
      status.value = `后端返回非JSON：${String(res.data).slice(0, 120)}`;
    }
  },
  fail: (err) => {
    console.error("[upload.fail]", err);
    uploading.value = false;
    status.value = `上传失败：${err?.errMsg || "unknown"}`;
  },
});
}
</script>
