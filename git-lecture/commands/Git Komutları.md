
git config get --global user.name
git config get --global user.email
git config set --global user.name
git config set --global user.email

git config set --global user.name 'Süleyman Önal'

ls -al

git add .

git commit -m 'first commit'

git branch

git rm dosya4 --cached (dosyayı silmez tekrar unstaged olur.)
git rm dosya4 -f (dosyayı siler.)

git add . && git commit -m '2nd commit'

git log --oneline

touch temp && git add . && git reset

git reflog

git reset --hard HEAD@{1}

| Komut | Commit İptal Edilir mi? | Staging Area Sıfırlanır mı? | Klasördeki Kodlar Silinir mi? |
| :--- | :---: | :---: | :---: |
| **`git reset --soft`** | Evet | **Hayır** (Staged kalır) | **Hayır** (Aynen kalır) |
| **`git reset`** (veya `--mixed`) | Evet | Evet (Unstaged olur) | **Hayır** (Aynen kalır) |
| **`git reset --hard`** | Evet | Evet | **EVET** (Silinir/Sıfırlanır) |

| Komut | Açıklama |
| :--- | :--- |
| `git remote -v` | Tanımlı tüm remote bağlantılarını ve URL'lerini listeler. |
| `git remote show origin` | `origin` bağlantısının tüm detaylarını (track edilen dallar vb.) gösterir. |
| `git remote add origin ` | Yeni bir `origin` bağlantısı ekler. |
| `git remote set-url origin ` | Var olan `origin` URL'sini değiştirir/günceller. |
| `git remote remove origin` | Tanımlı `origin` bağlantısını siler. |




git remote add origin git@github.com:suleymanonal/project1.git



| Komut / Kavram | Açıklama |
| :--- | :--- |
| **`upstream`** | Yerel dalın (local branch) bağlı olduğu uzak dal (remote branch) ilişkisidir. |
| **`git push -u origin `** | Kodları gönderir ve o dalı uzak sunucu ile ilişkilendirir (`-u` = `--set-upstream`). |
| **`push.autoSetupRemote`** | Yeni dallarda `upstream` bağlantısını manuel yazmadan otomatik kurmasını sağlayan Git ayarı. |

git push -u origin test
Yerel test branch'i ile GitHub'daki test branch'ini birbirine bağlar.

| Amaç / Senaryo | Tekil Dosya İçin | Klasör İçin (`-r`) |
| :--- | :--- | :--- |
| **Git takibinden ve diskten sil** | `git rm ` | `git rm -r ` |
| **Diskte tut, sadece Git takibinden çıkar** | `git rm --cached ` | `git rm -r --cached ` |
| **Değişiklik yapılmış ögeyi zorla (`force`) sil** | `git rm -f ` | `git rm -rf ` |
| **Takip edilmeyen (untracked) ögeyi diskten sil** | `rm ` | `rm -rf ` |


Yeni branch açıldıktan sonra remote a göndermek için
git push origin test

Peki remote üzerinde branch açarsak ve onu local e almak istersek ?

git fetch origin

git branch -a

git checkout dev

| Amaç / Adım | Komut |
| :--- | :--- |
| **1. Remote listesini güncelle** | `git fetch origin` |
| **2. Remote branch'i aynı isimle local'e al ve geç** | `git switch ` *(veya `git checkout `)* |
| **Remote'taki tüm branch'leri listele** | `git branch -r` |
| **Hem local hem remote branch'leri listele** | `git branch -a` |



1. Kodları Birleştirmeden Önce İncelemek (Güvenli Kontrol)

`git fetch`, uzak sunucudaki (remote) en son değişiklikleri ve commit geçmişini yerel veritabanına indiren, ancak **çalışma alanındaki (working directory) kodlara kesinlikle dokunmayan** güvenli bir senaryo komutudur.

2. Takım Arkadaşının Açtığı Branch'e Yerelde Bakmak / Test Etmek

# Yeni remote branch bilgisini çek
git fetch origin

# Remote branch'e geç ve local'de aktifleştir
git switch feature/payment

3. Uzak Sunucuda Silinen Dalları Temizlemek (--prune)

# Uzakta silinmiş dalların izlerini yerelden temizler
git fetch -p
# veya uzun haliyle:
git fetch --prune

4. git pull Yapmadan Önce Çakışma ve İlerleme Durumunu Görmek
# Haritayı güncelle
git fetch origin

# Durum raporunu al (Örn: Your branch is behind 'origin/main' by 3 commits)
git status


Örnek olarak remote da branch silindi diyelim fetch yapsak da local de kalmaya devam eder. prune gerekir. remote referanslar silinir.
git fetch --prune
Eğer silinen branch üzerindeysen local de kalmaya devam eder. branch değiştir ve 
git branch -d dev(silinecek branch)

Merge Mekanizması
Fast-Forward, hedef dalda hiçbir değişiklik yapılmadığında işaretçinin (pointer) sadece ileri kaydırılmasıdır. 3-Way Merge ise her iki dalda da bağımsız gelişmeler olduğunda Git'in 3 farklı commit noktasını karşılaştırıp yeni bir birleştirme commit'i (Merge Commit) oluşturmasıdır.

1. Senaryo: Fast-Forward Merge (İleriye Sarma)
Mantığı
master dalından test adında bir dal açtın. Sen test dalında çalışırken master dalında hiçbir yeni commit atılmadı. test'i master'a birleştirmek istediğinde Git bakar: "Arada hiç yol ayrımı oluşmamış, ben sadece master etiketini test'in durduğu en son commit'e kaydırayım."

# 1. 'test' dalına geç ve yeni bir dosya ekle
git switch test
echo "Fast-Forward için dosya" > ff-dosya.txt
git add ff-dosya.txt
git commit -m "feat: ff-dosya eklendi"

# 2. 'master' dalına geri dön (Bu süreçte master'a KESİNLİKLE yeni commit atma)
git switch master

# 3. Merge komutunu çalıştır
git merge test

Birleştirme Öncesi:
(master) ---------> C1 (70c500a)
                     \
(test)   -------------> C2 (a1b2c3d) [ff-dosya eklendi]

Birleştirme Sonrası (git merge test):
(master, test) ----> C1 ---> C2 (a1b2c3d)

2. Senaryo: 3-Way Merge (Üç Yönlü Birleştirme)
Mantığı
master dalından test adında bir dal açtın. Sen test dalında yeni işler yaparken, ekip arkadaşın da master dalına yeni bir commit attı (veya sen geçip master'a başka bir dosya ekledin). İki dal artık birbirinden dallandı/ayrıştı (diverged).

test'i master'a birleştirmek istediğinde Git tek başına ok kaydıramaz. Arka planda 3 noktayı karşılaştırır:

İki dalın ortak atası (Common Ancestor - dallanmanın başladığı ilk commit)

master dalının son hali

test dalının son hali

Git bu 3 noktayı sentezler ve geçmişi birleştiren otomatik bir Merge Commit oluşturur.

# 1. 'test' dalına geç ve bir dosya ekle
git switch test
echo "Test dalı değişikliği" > test-dosya.txt
git add test-dosya.txt
git commit -m "feat: test-dosya eklendi"

# 2. 'master' dalına dön VE master üzerinde de YENİ bir commit at (Dallanmayı sağla)
git switch master
echo "Master dalı değişikliği" > master-dosya.txt
git add master-dosya.txt
git commit -m "feat: master-dosya eklendi"

# 3. Şimdi 'master' içindeyken 'test' dalını merge et
git merge test

"Merge made by the 'ort' strategy"

# Git Merge Stratejileri: `ort` vs `recursive`

## `ort` (Ostensibly Recursive's Twin) Stratejisi
Git'in güncel sürümlerinde varsayılan olarak çalışan **3-Way Merge** algoritmasıdır.

### Temel Özellikleri
* **Açılımı:** Ostensibly Recursive's Twin
* **İşlevi:** İki dal arasındaki ortak atayı (common ancestor) bularak değişiklikleri sentezler ve otomatik Merge Commit oluşturur.
* **Avantajları:**
  1. Eski `recursive` stratejisine kıyasla devasa projelerde **100x-1000x daha hızlıdır**.
  2. Dosya taşıma ve yeniden adlandırma (Rename) işlemlerini otomatik algılamada çok başarılıdır.
  3. Çakışma (Merge Conflict) yönetiminde daha az hata yapar.


1. Senaryo: Çakışmayı (Conflict) Elle Oluşturalım
Önce master dalında ortak-kod.txt adında bir dosya oluşturup commit edelim:

git switch master
echo "Satir 1: Orijinal Baslik" > ortak-kod.txt
git add ortak-kod.txt
git commit -m "chore: orijinal dosya eklendi"

Feature Dalı Aç ve Aynı Satırı Değiştir

git switch -c feature
echo "Satir 1: Feature Ekibinin Basligi" > ortak-kod.txt
git add ortak-kod.txt
git commit -m "feat: feature basligi guncellendi"

Master Dalına Dön ve Aynı Satırı Farklı Değiştir

git switch master
echo "Satir 1: Master Ekibinin Basligi" > ortak-kod.txt
git add ortak-kod.txt
git commit -m "feat: master basligi guncellendi"

git merge feature  (on master branch)

Çakışmayı Çözme Yöntemleri (3 Farklı Yaklaşım)
1.
ilk satıra şunu yaz --> Satir 1: Master ve Feature Birlesik Basligi
git add ortak-kod.txt
git commit -m "fix: merge conflict cozuldu"

2. 
Tek Komutla Taraf Seçme (--ours veya --theirs)

Bizim Kodu Tut (--ours): Bulunduğun dalın (master) kodunu kabul eder.
git checkout --ours ortak-kod.txt
git add ortak-kod.txt
git commit -m "fix: master kodlari korundu"

Onların Kodunu Tut (--theirs): Gelen dalın (feature) kodunu kabul eder.
git checkout --theirs ortak-kod.txt
git add ortak-kod.txt
git commit -m "fix: feature kodlari kabul edildi"

3.
İşlemi Tamamen İptal Etmek (--abort)
git merge --abort

Manuel düzeltmelerde git add ve git commit yeterli olur.

Rebase

git rebase, bir dalın (branch) başlangıç tabanını (base) alıp başka bir commit'in üzerine yeniden oturtma (re-base) işlemidir.

Aynı amacı taşıdığı git merge gibi iki dalı birleştirir; ancak commit geçmişini (log) şekillendirme biçimleri birbirinden tamamen farklıdır.

Altın Kuralın Derinlemesine ve Basit Açıklaması
⚠️ Altın Kural: Uzak sunucuya (origin) gönderilmiş ve başkalarının da üzerinde çalıştığı ortak dallarda KESİNLİKLE rebase yapılmaz.

Neden? İşin Mantığı Çok Basit:
Git'te her commit'in kendine has bir kimlik numarası (Hash) vardır (a1b2c3d gibi).

Siz rebase yaptığınızda Git aslında var olan commit'leri siler ve yeni bastığı zeminin üzerine aynı içerikte ama YENİ KİMLİK NUMARALI (x9y8z7w) yepyeni commit'ler basar.

Gerçek Hayat Meselesi:
Siz ve arkadaşınız Ahmet, sunucudaki dev dalında çalışıyorsunuz. Ahmet sunucudaki C1 commit'ini baz alarak kendi kodunu yazmaya başladı.

Siz yerelinizde dev dalına rebase attınız. Git, C1 commit'ini sildi, yerine C1_YENİ commit'ini koydu ve siz bunu sunucuya zorla (git push --force) gönderdiniz.

Ahmet kendi kodunu push etmek istediğinde Git patlar! Çünkü Ahmet'in bilgisayarındaki geçmiş ile sunucudaki geçmiş tamamen kopmuştur. Ahmet'in "üzerine bina inşa ettiği zemin" siz rebase attığınız için yok olmuştur.

Özetle: Rebase geçmişi yeniden yazar. Kendi kişisel bilgisayarınızdaki (local) geçmişi istediğiniz gibi yeniden yazabilirsiniz; ancak başkalarının da okuduğu "ortak kitabı" yeniden yazarsanız herkesin kafa karışır ve kodlar çöp olur.

1. Master Dalında Başlangıç Commit'i At

git switch master
echo "Satir 1: Uygulama Baslatildi" > app.txt
git add app.txt
git commit -m "chore: uygulama baslatildi"

2. Feature Dalı Aç ve Geliştirme Yap

git switch -c feature/login
echo "Satir 2: Login Ekranı Kodlandi" >> app.txt
git add app.txt
git commit -m "feat: login ekrani eklendi"

3. Master Dalına Dön ve Oraya da Yeni Commit At

git switch master
echo "Satir 2: Master Alt Yapi Guncellendi" >> app.txt
git add app.txt
git commit -m "fix: master altyapisi guncellendi"

4. Feature Dalına Geç ve Rebase Başlat

git switch feature/login
git rebase master

5. Çakışmayı (Conflict) Çöz ve Devam Et

Satir 1: Uygulama Baslatildi
Satir 2: Master Alt Yapi Guncellendi
Satir 3: Login Ekranı Kodlandi

6. Kritik Nokta: Sakın git commit ATMAYIN! Çakışmayı çözdükten sonra:

git add app.txt
git rebase --continue

git log --oneline --graph

Geçmiş tamamen lineer (dümdüz) bir çizgi halinde ilerler.

# Rebase Nedir? Altın Kural ve Adım Adım Senaryo

## Altın Kural (Golden Rule)
> **Uzak sunucuya (`origin`) push edilmiş ve ortak kullanılan dallarda KESİNLİKLE `rebase` yapılmaz.**

* **Nedeni:** Rebase var olan commit'leri siler ve aynı içerikle yeni kimlikli (hash) commit'ler oluşturur. Geçmişi yeniden yazdığı için diğer geliştiricilerin yerel veritabanları ile sunucunun bağı kopar.
* **Nerede Kullanılır?** Sadece kendi bilgisayarınızdaki kişisel (local) branch'lerinizde kullanılır.





Merhaba arkadaşlar,

Eğitimdeki uygulamalı lab çalışmaları için aşağıdaki kurulumları eğitim öncesinde tamamlamanız gerekmektedir:

**Terminal Ortamı** • **Mac:** Dahili **Terminal** yeterlidir. • **Windows:** **Git Bash**, **PowerShell** veya **Windows Terminal** kullanabilirsiniz. _(Linux komut uyumluluğu için **Git Bash** önerilir)._

**Kurulacak Yazılımlar**

1. **Git:** [https://git-scm.com/](https://git-scm.com/) _(Windows kurulumunda **Git Bash** seçeneğini işaretleyin)_
    
2. **VS Code:** [https://code.visualstudio.com/](https://code.visualstudio.com/)  (Veya alternatifi)
    
3. **Docker Desktop:** [https://www.docker.com/products/docker-desktop/](https://www.docker.com/products/docker-desktop/)
    
    _(Kurulum sonrası **Settings > Kubernetes** altından **"Enable Kubernetes"** seçeneğini açın. `kubectl` otomatik yüklenecektir)._
    
4. **Helm v3:**
    
    • **Windows:** PowerShell veya Git Bash terminalinden `winget install Helm.Helm`
    
    • **Mac:** Terminalden `brew install helm`
    

**Docker Ayarı (Önemli)** Docker Desktop ayarlarından (**Settings > Resources**) Docker'a en az **4 GB RAM** ayırmayı unutmayın.

**Kurulum Kontrolü** Terminalinizde sırayla şu komutları çalıştırıp test edin:

git --version
docker --version
docker run hello-world
kubectl version --client
helm version