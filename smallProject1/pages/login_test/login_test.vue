<template>
  <view style="padding: 24px;">
    <button type="primary" @click="getCode" style="height: 88px; font-size: 22px;">
      获取登录 code
    </button>

    <view v-if="code" style="margin-top: 16px; font-size: 14px; word-break: break-all;">
      code：{{ code }}
    </view>

    <view v-if="errMsg" style="margin-top: 16px; font-size: 14px;">
      失败：{{ errMsg }}
    </view>
  </view>
</template>

<script setup>
import { ref } from "vue";

const code = ref("");
const errMsg = ref("");

function getCode() {
  code.value = "";
  errMsg.value = "";

  uni.login({
    provider: "weixin",
    success: (res) => {
      console.log("uni.login success:", res);
      code.value = res.code || "";
      if (!code.value) errMsg.value = "没有拿到 code（res.code 为空）";
    },
    fail: (err) => {
      console.log("uni.login fail:", err);
      errMsg.value = JSON.stringify(err);
    },
  });
}
</script>
