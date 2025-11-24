package scan

import (
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// ProgressSpinner shows scanning progress with a spinning animation
type ProgressSpinner struct {
	processed  int64
	discovered int64
	mu         sync.Mutex
	ticker     *time.Ticker
	done       chan bool
	startTime  time.Time
}

// NewProgressSpinner creates and starts a new progress spinner
func NewProgressSpinner() *ProgressSpinner {
	s := &ProgressSpinner{
		ticker:    time.NewTicker(100 * time.Millisecond),
		done:      make(chan bool),
		startTime: time.Now(),
	}

	go s.animate()

	return s
}

// animate runs the spinner animation in a background goroutine
func (s *ProgressSpinner) animate() {
	// Unicode braille spinner characters
	chars := []string{"⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"}
	i := 0

	for {
		select {
		case <-s.ticker.C:
			s.mu.Lock()
			processed := atomic.LoadInt64(&s.processed)
			discovered := atomic.LoadInt64(&s.discovered)
			fmt.Printf("\r%s Scanning: %s / %s items processed",
				chars[i],
				formatNumber(processed),
				formatNumber(discovered))
			s.mu.Unlock()
			i = (i + 1) % len(chars)
		case <-s.done:
			return
		}
	}
}

// IncrementProcessed increments the processed counter
func (s *ProgressSpinner) IncrementProcessed() {
	atomic.AddInt64(&s.processed, 1)
}

// IncrementDiscovered increments the discovered counter by n
func (s *ProgressSpinner) IncrementDiscovered(n int) {
	atomic.AddInt64(&s.discovered, int64(n))
}

// Stop stops the spinner and prints the final summary
func (s *ProgressSpinner) Stop() {
	s.ticker.Stop()
	s.done <- true

	processed := atomic.LoadInt64(&s.processed)
	elapsed := time.Since(s.startTime)

	s.mu.Lock()
	fmt.Printf("\r✓ Scanned %s items in %.1fs\n",
		formatNumber(processed),
		elapsed.Seconds())
	s.mu.Unlock()
}

// formatNumber formats a number with thousand separators
func formatNumber(n int64) string {
	if n < 1000 {
		return fmt.Sprintf("%d", n)
	}

	// Format with commas
	str := fmt.Sprintf("%d", n)
	result := ""
	for i, c := range str {
		if i > 0 && (len(str)-i)%3 == 0 {
			result += ","
		}
		result += string(c)
	}
	return result
}
