<template>
  <div id="app">
    <GlobalError />
    <nav class="nav">
      <router-link to="/">每日夸夸</router-link>
      <router-link to="/chat">聊天陪伴</router-link>
      <router-link to="/settings">设置</router-link>
    </nav>
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import GlobalError from '@/components/GlobalError.vue'
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  background: #f5f5f5;
  color: #333;
}

#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.nav {
  display: flex;
  gap: 20px;
  padding: 16px 24px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.nav a {
  text-decoration: none;
  color: #666;
  font-weight: 500;
  padding: 8px 16px;
  border-radius: 8px;
  transition: all 0.2s;
}

.nav a:hover,
.nav a.router-link-active {
  background: #e8f4ff;
  color: #1890ff;
}

.main-content {
  flex: 1;
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}
</style>
