<template>
  <div 
    class="skeleton-loader" 
    :style="{ 
      width: width, 
      height: height, 
      borderRadius: borderRadius 
    }"
  ></div>
</template>

<script>
export default {
  name: 'SkeletonLoader',
  props: {
    width: {
      type: String,
      default: '100%'
    },
    height: {
      type: String,
      default: '16px'
    },
    borderRadius: {
      type: String,
      default: '8px'
    }
  }
}
</script>

<style scoped>
.skeleton-loader {
  background: linear-gradient(
    90deg,
    var(--md-sys-color-surface-thick) 25%,
    rgba(120, 120, 128, 0.12) 37%,
    var(--md-sys-color-surface-thick) 63%
  );
  background-size: 400% 100%;
  animation: shimmer 1.4s ease infinite;
}

@keyframes shimmer {
  0% {
    background-position: 100% 50%;
  }
  100% {
    background-position: 0 50%;
  }
}

/* Dark mode adjustment if needed, but the css vars should handle it */
</style>
