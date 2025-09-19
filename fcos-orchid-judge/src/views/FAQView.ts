import { FCOSOrchidJudgeWidget } from '../widget'

export class FAQView {
  constructor(private widget: FCOSOrchidJudgeWidget) {}

  render(): string {
    const faqItems = [
      {
        question: 'How is Form / Symmetry / Balance scored?',
        answer: 'Form scoring evaluates the overall shape, symmetry, and balance of the flower. Points are awarded for well-proportioned petals, proper flower positioning, and bilateral symmetry. Educational scoring helps you understand ideal orchid characteristics.'
      },
      {
        question: 'How is Color & Saturation scored?',
        answer: 'Color scoring assesses the intensity, clarity, and appeal of flower colors. Vibrant, clear colors with good contrast typically score higher. The AI analyzes color distribution and saturation levels across the bloom.'
      },
      {
        question: 'How is Size & Substance scored?',
        answer: 'Size considers flower dimensions relative to the species standard, while substance evaluates the thickness and quality of petals and sepals. Flowers with good substance appear fuller and more durable.'
      },
      {
        question: 'How is Floriferousness & Arrangement scored?',
        answer: 'This category evaluates the number of flowers, spike quality, and overall presentation. More flowers arranged well on strong spikes typically score higher. The arrangement should be balanced and attractive.'
      },
      {
        question: 'How is Condition & Grooming scored?',
        answer: 'Condition scoring looks at the health and freshness of the flowers, while grooming considers plant cleanliness and presentation. Fresh, unblemished flowers on clean plants score best.'
      },
      {
        question: 'How is Distinctiveness / Impression scored?',
        answer: 'This subjective category rewards exceptional characteristics that make the orchid stand out. Unique color patterns, unusual forms, or exceptional quality can earn high distinctiveness scores.'
      },
      {
        question: 'Is this official judging?',
        answer: 'No, this is an educational tool only. It does not provide official awards from AOS, AOC, RHS, or any recognized orchid organization. Results are for learning and practice purposes only.'
      },
      {
        question: 'Do my photos upload automatically?',
        answer: 'Photos stay on your device by default. Cloud sync only occurs if you enable it in Profile settings and provide the required cloud configuration. You have full control over your data.'
      },
      {
        question: 'What is Hybrid Analysis?',
        answer: 'Hybrid analysis identifies grex names (hybrid group names) and attempts to lookup parentage information. When available, it provides breeding history and related awards to help understand the hybrid\'s background.'
      },
      {
        question: 'How do I export my results?',
        answer: 'From any entry, you can export certificates as PNG images, detailed scoring as CSV files, or narrative reports as TXT files. Use the share button to email or save results to your device.'
      },
      {
        question: 'Can I track progress over multiple years?',
        answer: 'Yes! The app maintains a history of your entries, allowing you to track improvements and compare results over time. Your data persists on your device until you clear it or the app is uninstalled.'
      }
    ]

    return `
      <div class="space-y-6">
        <!-- Header -->
        <div class="flex items-center gap-3 mb-6">
          <button class="btn btn-outline" data-action="back">← Back</button>
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">Frequently Asked Questions</h2>
        </div>

        <!-- FAQ Items -->
        <div class="space-y-2">
          ${faqItems.map((item, index) => this.renderFAQItem(item, index)).join('')}
        </div>

        <!-- Additional Help -->
        <div class="card bg-gray-50 dark:bg-gray-800">
          <h3 class="font-semibold text-gray-900 dark:text-white mb-2">
            Need More Help?
          </h3>
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
            This tool is provided by the Five Cities Orchid Society for educational purposes. 
            For technical support or questions about orchid care, visit our website or contact local orchid societies.
          </p>
          <div class="flex gap-2">
            <button class="btn btn-outline btn-sm" data-action="about">
              About FCOS
            </button>
            <button class="btn btn-outline btn-sm" data-action="profile">
              Run Diagnostics
            </button>
          </div>
        </div>
      </div>
    `
  }

  private renderFAQItem(item: { question: string; answer: string }, index: number): string {
    return `
      <div class="card">
        <button class="w-full text-left" data-action="toggle-faq" data-index="${index}">
          <div class="flex items-center justify-between">
            <h3 class="font-medium text-gray-900 dark:text-white pr-4">
              ${item.question}
            </h3>
            <span class="faq-icon text-gray-400 transform transition-transform duration-200">
              ▼
            </span>
          </div>
        </button>
        
        <div class="faq-answer hidden mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <p class="text-sm text-gray-600 dark:text-gray-400">
            ${item.answer}
          </p>
        </div>
      </div>
    `
  }

  mount(container: HTMLElement): void {
    // Set up event listeners
    const backBtn = container.querySelector('[data-action="back"]')
    const aboutBtn = container.querySelector('[data-action="about"]')
    const profileBtn = container.querySelector('[data-action="profile"]')
    
    backBtn?.addEventListener('click', () => this.widget.goBack())
    aboutBtn?.addEventListener('click', () => this.widget.navigateTo('about'))
    profileBtn?.addEventListener('click', () => this.widget.navigateTo('profile'))

    // FAQ toggle functionality
    container.querySelectorAll('[data-action="toggle-faq"]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const button = e.currentTarget as HTMLElement
        const card = button.closest('.card')
        const answer = card?.querySelector('.faq-answer')
        const icon = card?.querySelector('.faq-icon')
        
        if (answer && icon) {
          const isHidden = answer.classList.contains('hidden')
          
          if (isHidden) {
            answer.classList.remove('hidden')
            icon.classList.add('rotate-180')
          } else {
            answer.classList.add('hidden')
            icon.classList.remove('rotate-180')
          }
        }
      })
    })
  }
}