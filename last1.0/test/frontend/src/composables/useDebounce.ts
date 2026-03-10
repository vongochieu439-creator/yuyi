import { ref } from 'vue'

export function useDebounce(delay: number = 300) {
  const timer = ref<ReturnType<typeof setTimeout> | null>(null)

  const debounce = (fn: () => void) => {
    if (timer.value) clearTimeout(timer.value)
    timer.value = setTimeout(fn, delay)
  }

  const cancel = () => {
    if (timer.value) {
      clearTimeout(timer.value)
      timer.value = null
    }
  }

  return { debounce, cancel }
}
