"""
visualizer.py - Sonuçları Görselleştirme Modülü
=================================================
Matplotlib kullanarak saldırı ve benchmark sonuçlarını
grafiklerle görselleştirir.

Tersine Mühendislik Dersi - Vize Projesi
"""

import matplotlib
matplotlib.use('Agg')  # GUI olmadan çalışmak için
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import os
from typing import Dict, List, Optional


class ResultVisualizer:
    """Sonuç görselleştirme aracı."""

    def __init__(self, output_dir: str = "results"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Stil ayarları
        plt.style.use('default')
        self.colors = {
            'unsalted': '#e74c3c',    # Kırmızı (güvensiz)
            'salted': '#2ecc71',      # Yeşil (güvenli)
            'blake3': '#3498db',      # Mavi
            'sha256': '#f39c12',      # Turuncu
            'warning': '#e74c3c',
            'success': '#2ecc71',
        }

    # ------------------------------------------------------------------ #
    #  1. Salt'lı vs Salt'sız Saldırı Süresi
    # ------------------------------------------------------------------ #
    def plot_attack_comparison(
        self,
        unsalted_result: Dict,
        salted_result: Dict,
        title: str = "Salt'lı vs Salt'sız: Saldırı Süresi Karşılaştırması",
        filename: str = "attack_comparison.png"
    ) -> str:
        """Saldırı süresi karşılaştırma grafiği."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle(title, fontsize=14, fontweight='bold', y=1.02)

        # Sol: Süre karşılaştırması
        ax1 = axes[0]
        methods = ['Salt\'sız', 'Salt\'lı']
        times = [unsalted_result['time_seconds'], salted_result['time_seconds']]
        bars = ax1.bar(methods, times, color=[self.colors['unsalted'], self.colors['salted']],
                       width=0.5, edgecolor='black', linewidth=0.5)
        ax1.set_ylabel('Süre (saniye)', fontsize=11)
        ax1.set_title('Saldırı Süresi', fontsize=12)
        for bar, t in zip(bars, times):
            ax1.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + max(times) * 0.02,
                     f'{t:.4f}s', ha='center', va='bottom', fontsize=10, fontweight='bold')

        # Sağ: Deneme sayısı
        ax2 = axes[1]
        attempts = [unsalted_result['attempts'], salted_result['attempts']]
        bars2 = ax2.bar(methods, attempts, color=[self.colors['unsalted'], self.colors['salted']],
                        width=0.5, edgecolor='black', linewidth=0.5)
        ax2.set_ylabel('Deneme Sayısı', fontsize=11)
        ax2.set_title('Toplam Hash Hesaplaması', fontsize=12)
        for bar, a in zip(bars2, attempts):
            ax2.text(bar.get_x() + bar.get_width() / 2., bar.get_height() + max(attempts) * 0.02,
                     f'{a:,}', ha='center', va='bottom', fontsize=10, fontweight='bold')

        plt.tight_layout()
        path = os.path.join(self.output_dir, filename)
        fig.savefig(path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return path

    # ------------------------------------------------------------------ #
    #  2. Rainbow Table Etkisi
    # ------------------------------------------------------------------ #
    def plot_rainbow_table_effect(
        self,
        unsalted_multi: Dict,
        salted_multi: Dict,
        filename: str = "rainbow_table_effect.png"
    ) -> str:
        """Rainbow table saldırısı vs Salt'lı saldırı karşılaştırması."""
        fig, ax = plt.subplots(figsize=(12, 6))

        categories = ['Hazırlık\n(Rainbow Table / -)', 'Arama / Saldırı\nSüresi', 'TOPLAM\nSüre']

        unsalted_vals = [
            unsalted_multi.get('rainbow_build_time', 0),
            unsalted_multi.get('total_lookup_time', 0),
            unsalted_multi.get('total_time', 0),
        ]
        salted_vals = [
            0,  # Salt'lı için rainbow table yok
            salted_multi.get('total_time', 0),
            salted_multi.get('total_time', 0),
        ]

        x = np.arange(len(categories))
        width = 0.3

        bars1 = ax.bar(x - width / 2, unsalted_vals, width, label='Salt\'sız (Rainbow Table)',
                       color=self.colors['unsalted'], edgecolor='black', linewidth=0.5)
        bars2 = ax.bar(x + width / 2, salted_vals, width, label='Salt\'lı (Her kullanıcı ayrı)',
                       color=self.colors['salted'], edgecolor='black', linewidth=0.5)

        ax.set_ylabel('Süre (saniye)', fontsize=11)
        ax.set_title(f'Çoklu Kullanıcı Saldırısı: Rainbow Table Etkisi\n'
                     f'({unsalted_multi["total_users"]} kullanıcı)',
                     fontsize=13, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(categories, fontsize=10)
        ax.legend(fontsize=10)

        # Değer etiketleri
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                if height > 0:
                    ax.text(bar.get_x() + bar.get_width() / 2., height,
                            f'{height:.4f}s', ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        path = os.path.join(self.output_dir, filename)
        fig.savefig(path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return path

    # ------------------------------------------------------------------ #
    #  3. BLAKE3 vs SHA-256
    # ------------------------------------------------------------------ #
    def plot_blake3_vs_sha256(
        self,
        benchmark_data: Dict,
        filename: str = "blake3_vs_sha256.png"
    ) -> str:
        """BLAKE3 ve SHA-256 performans karşılaştırma grafiği."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle('BLAKE3 vs SHA-256 Performans Karşılaştırması',
                     fontsize=14, fontweight='bold', y=1.02)

        b3 = benchmark_data['blake3']
        s256 = benchmark_data['sha256']

        # Sol: Hash/saniye
        ax1 = axes[0]
        categories = ['Salt\'sız', 'Salt\'lı']
        blake3_hps = [b3['unsalted_hps'], b3['salted_hps']]
        sha256_hps = [s256['unsalted_hps'], s256['salted_hps']]

        x = np.arange(len(categories))
        width = 0.3
        ax1.bar(x - width / 2, blake3_hps, width, label='BLAKE3', color=self.colors['blake3'],
                edgecolor='black', linewidth=0.5)
        ax1.bar(x + width / 2, sha256_hps, width, label='SHA-256', color=self.colors['sha256'],
                edgecolor='black', linewidth=0.5)
        ax1.set_ylabel('Hash / Saniye', fontsize=11)
        ax1.set_title('Hashing Hızı', fontsize=12)
        ax1.set_xticks(x)
        ax1.set_xticklabels(categories)
        ax1.legend()
        ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))

        # Sağ: Toplam süre
        ax2 = axes[1]
        blake3_times = [b3['unsalted_seconds'], b3['salted_seconds']]
        sha256_times = [s256['unsalted_seconds'], s256['salted_seconds']]

        ax2.bar(x - width / 2, blake3_times, width, label='BLAKE3', color=self.colors['blake3'],
                edgecolor='black', linewidth=0.5)
        ax2.bar(x + width / 2, sha256_times, width, label='SHA-256', color=self.colors['sha256'],
                edgecolor='black', linewidth=0.5)
        ax2.set_ylabel('Süre (saniye)', fontsize=11)
        ax2.set_title(f'Toplam Süre ({benchmark_data["iterations"]:,} iterasyon)', fontsize=12)
        ax2.set_xticks(x)
        ax2.set_xticklabels(categories)
        ax2.legend()

        plt.tight_layout()
        path = os.path.join(self.output_dir, filename)
        fig.savefig(path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return path

    # ------------------------------------------------------------------ #
    #  4. Salt Uzunluğu Etkisi
    # ------------------------------------------------------------------ #
    def plot_salt_length_impact(
        self,
        salt_data: Dict,
        filename: str = "salt_length_impact.png"
    ) -> str:
        """Salt uzunluğunun güvenlik üzerindeki etkisi grafiği."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        fig.suptitle('Salt Uzunluğunun Güvenlik ve Performans Etkisi',
                     fontsize=14, fontweight='bold', y=1.02)

        results = salt_data['results']
        lengths = sorted(results.keys())
        bits = [results[l]['salt_bits'] for l in lengths]
        hps = [results[l]['hashes_per_second'] for l in lengths]

        # Sol: Hash hızına etkisi
        ax1 = axes[0]
        ax1.plot(bits, hps, 'o-', color=self.colors['blake3'], linewidth=2, markersize=8)
        ax1.set_xlabel('Salt Uzunluğu (bit)', fontsize=11)
        ax1.set_ylabel('Hash / Saniye', fontsize=11)
        ax1.set_title('Salt Uzunluğu vs Hash Hızı', fontsize=12)
        ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
        ax1.grid(True, alpha=0.3)

        # Sağ: Keyspace (güvenlik gücü)
        ax2 = axes[1]
        keyspace_log = [l * 8 for l in lengths]  # 2^(bits) olarak
        ax2.bar([str(b) for b in bits], keyspace_log,
                color=self.colors['salted'], edgecolor='black', linewidth=0.5)
        ax2.set_xlabel('Salt Uzunluğu (bit)', fontsize=11)
        ax2.set_ylabel('Keyspace (2^n olası değer)', fontsize=11)
        ax2.set_title('Salt Keyspace Büyüklüğü', fontsize=12)

        for i, (b, k) in enumerate(zip(bits, keyspace_log)):
            ax2.text(i, k + 2, f'2^{k}', ha='center', fontsize=9, fontweight='bold')

        plt.tight_layout()
        path = os.path.join(self.output_dir, filename)
        fig.savefig(path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return path

    # ------------------------------------------------------------------ #
    #  5. Saldırı Süresi Projeksiyonu
    # ------------------------------------------------------------------ #
    def plot_crack_time_estimation(
        self,
        estimations: List[Dict],
        filename: str = "crack_time_estimation.png"
    ) -> str:
        """Farklı şifre uzunlukları için kırılma süresi projeksiyonu."""
        fig, ax = plt.subplots(figsize=(12, 7))

        lengths = [e['password_length'] for e in estimations]
        unsalted_times = [e['unsalted']['total_seconds'] for e in estimations]
        salted_times = [e['salted']['total_seconds'] for e in estimations]

        ax.semilogy(lengths, unsalted_times, 'o-', color=self.colors['unsalted'],
                    linewidth=2, markersize=8, label='Salt\'sız (Rainbow Table)')
        ax.semilogy(lengths, salted_times, 's-', color=self.colors['salted'],
                    linewidth=2, markersize=8, label='Salt\'lı (Bireysel Saldırı)')

        ax.set_xlabel('Şifre Uzunluğu (karakter)', fontsize=11)
        ax.set_ylabel('Tahmini Kırılma Süresi (saniye, log ölçek)', fontsize=11)
        ax.set_title(f'Şifre Kırılma Süresi Projeksiyonu\n'
                     f'({estimations[0]["num_users"]} kullanıcı, {estimations[0]["charset_size"]} karakterlik alfabe)',
                     fontsize=13, fontweight='bold')
        ax.legend(fontsize=11)
        ax.grid(True, alpha=0.3, which='both')
        ax.set_xticks(lengths)

        # Zaman referans çizgileri
        time_refs = {
            '1 dakika': 60,
            '1 saat': 3600,
            '1 gün': 86400,
            '1 yıl': 365.25 * 86400,
            '100 yıl': 100 * 365.25 * 86400,
        }
        for label, seconds in time_refs.items():
            if min(unsalted_times + salted_times) < seconds < max(unsalted_times + salted_times) * 10:
                ax.axhline(y=seconds, color='gray', linestyle='--', alpha=0.5)
                ax.text(lengths[-1] + 0.1, seconds, label, fontsize=8, color='gray', va='center')

        plt.tight_layout()
        path = os.path.join(self.output_dir, filename)
        fig.savefig(path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return path

    # ------------------------------------------------------------------ #
    #  6. Aynı Şifre - Farklı Hash Gösterimi
    # ------------------------------------------------------------------ #
    def plot_same_password_different_hashes(
        self,
        password: str,
        unsalted_hashes: List[str],
        salted_hashes: List[str],
        filename: str = "same_password_hashes.png"
    ) -> str:
        """Aynı şifrenin salt'lı ve salt'sız hash farklılığını gösterir."""
        fig, axes = plt.subplots(2, 1, figsize=(14, 8))
        fig.suptitle(f'Aynı Şifre ("{password}") - Hash Çeşitliliği Karşılaştırması',
                     fontsize=14, fontweight='bold')

        # Üst: Salt'sız (hep aynı)
        ax1 = axes[0]
        ax1.set_title('[GUVENLI DEGIL] Salt\'siz Hash (Her seferinde AYNI)', fontsize=12, color=self.colors['unsalted'])
        for i, h in enumerate(unsalted_hashes):
            ax1.text(0.02, 0.85 - i * 0.18, f'Kullanıcı {i + 1}: {h[:48]}...',
                     fontsize=9, family='monospace', transform=ax1.transAxes,
                     color=self.colors['unsalted'])
        ax1.set_xlim(0, 1)
        ax1.set_ylim(0, 1)
        ax1.axis('off')

        # Alt: Salt'lı (hep farklı)
        ax2 = axes[1]
        ax2.set_title('[GUVENLI] Salt\'li Hash (Her seferinde FARKLI)', fontsize=12, color=self.colors['salted'])
        for i, h in enumerate(salted_hashes):
            ax2.text(0.02, 0.85 - i * 0.18, f'Kullanıcı {i + 1}: {h[:48]}...',
                     fontsize=9, family='monospace', transform=ax2.transAxes,
                     color=self.colors['salted'])
        ax2.set_xlim(0, 1)
        ax2.set_ylim(0, 1)
        ax2.axis('off')

        plt.tight_layout()
        path = os.path.join(self.output_dir, filename)
        fig.savefig(path, dpi=150, bbox_inches='tight')
        plt.close(fig)
        return path
