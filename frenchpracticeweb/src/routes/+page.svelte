<!-- src/routes/+page.svelte -->
<script lang="ts">
  import { tick } from 'svelte';

  type Question = {
    id: string;
    url: string;
    expected: number | null;
  };

  let q: Question | null = null;
  let inputValue = '';
  let audioEl: HTMLAudioElement | null = null;

  let total = 0;
  let correct = 0;
  let lastResult: 'correct' | 'wrong' | null = null;
  let lastExpected: number | null = null;

  async function nextQuestion() {
    lastResult = null;
    lastExpected = null;
    inputValue = '';

    const res = await fetch('/api/question');
    if (!res.ok) {
      const text = await res.text();
      alert(`API error: ${text}`);
      return;
    }
    q = await res.json();

    await tick(); // 等 DOM 更新
    if (audioEl && q?.url) {
      audioEl.load();
      // 瀏覽器通常要求「使用者手勢」才能播放
      // 所以建議用按鈕觸發 nextQuestion()
      try {
        await audioEl.play();
      } catch {
        // 若被 autoplay 擋住，使用者按重播即可
      }
    }
  }

  async function replay() {
    if (!audioEl) return;
    audioEl.currentTime = 0;
    try {
      await audioEl.play();
    } catch {}
  }

  async function submit() {
    if (!q) return;

    const guess = Number.parseInt(inputValue.trim(), 10);
    total += 1;

    const ok = q.expected !== null && guess === q.expected;
    if (ok) correct += 1;

    lastResult = ok ? 'correct' : 'wrong';
    lastExpected = q.expected;

    // ✅ 答對：直接下一題並播放
    if (ok) {
      await nextQuestion();
    }
  }

  $: accuracy = total ? Math.round((correct / total) * 1000) / 10 : 0; // 1 decimal
</script>

<main style="max-width: 720px; margin: 40px auto; padding: 0 16px; font-family: system-ui;">
  <h1>French Number Dictation (0–99)</h1>

  <div style="display:flex; gap:12px; align-items:center; flex-wrap:wrap; margin: 12px 0 20px;">
    <button on:click={nextQuestion}>下一題（出題 + 播放）</button>
    <button on:click={replay} disabled={!q}>重播</button>

    <div style="margin-left:auto;">
      <b>Correct:</b> {correct} / {total} &nbsp; <b>Accuracy:</b> {accuracy}%
    </div>
  </div>

  {#if q}
    <audio bind:this={audioEl} controls src={q.url} style="width:100%; margin-bottom: 16px;"></audio>

    <div style="display:flex; gap:12px; align-items:center; flex-wrap:wrap;">
      <input
        placeholder="輸入你聽到的數字（例如 7）"
        bind:value={inputValue}
        inputmode="numeric"
        style="padding:10px; font-size:16px; width: 260px;"
        on:keydown={async (e) => {
            if (e.key === 'Enter') {
            e.preventDefault();   // 避免某些情況下觸發其他預設行為
            await submit();
            }
        }}
      />
      <button on:click={submit}>送出</button>
    </div>

    {#if lastResult}
      <p style="margin-top: 14px;">
        {#if lastResult === 'correct'}
          ✅ 正確！
        {:else}
          ❌ 不對。正確答案是：<b>{lastExpected ?? '(unknown)'}</b>
        {/if}
      </p>
    {/if}
  {:else}
    <p>按「下一題」開始。</p>
  {/if}
</main>
