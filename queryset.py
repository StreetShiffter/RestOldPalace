from django.shortcuts import render, get_object_or_404
from django.db.models import (
    Q, Count, Avg, Max, Min, Sum, Upper, Lower, Concat, Value, F
)
from django.db.models.functions import Coalesce
from .models import Book
import json


def book_full_demo_view(request):
    """
    Демонстрационный FBV со ВСЕМИ основными возможностями Django ORM.
    Используйте этот контроллер как шпаргалку — копируйте нужные блоки.
    """

# === 1. БАЗОВАЯ ЗАГРУЗКА ВСЕХ ОБЪЕКТОВ ===
    all_books = Book.objects.all()  # QuerySet: SELECT * FROM book

# === 2. ФИЛЬТРАЦИЯ: lookup'ы (аналоги WHERE) ===

    # ТОЧНОЕ СОВПАДЕНИЕ
    exact_books = Book.objects.filter(title__exact='1984')  # title = '1984'

    # РЕГИСТРОНЕЗАВИСИМОЕ ТОЧНОЕ СОВПАДЕНИЕ
    iexact_books = Book.objects.filter(author__iexact='пушкин')  # author ILIKE 'пушкин'

    # СОДЕРЖИТ ПОДСТРОКУ
    contains_books = Book.objects.filter(title__contains='война')  # title LIKE '%война%'

    # СОДЕРЖИТ (без учёта регистра)
    icontains_books = Book.objects.filter(title__icontains='ВОЙНА')  # title ILIKE '%война%'

    # НАЧИНАЕТСЯ С
    startswith_books = Book.objects.filter(author__startswith='Лев')  # author LIKE 'Лев%'

    # НАЧИНАЕТСЯ С (без регистра)
    istartswith_books = Book.objects.filter(author__istartswith='лев')  # author ILIKE 'лев%'

    # ЗАКАНЧИВАЕТСЯ НА
    endswith_books = Book.objects.filter(title__endswith='...')  # title LIKE '%...'

    # ЗАКАНЧИВАЕТСЯ НА (без регистра)
    iendswith_books = Book.objects.filter(title__iendswith='...')  # title ILIKE '%...'

    # ВХОДИТ В СПИСОК
    in_books = Book.objects.filter(id__in=[1, 2, 3])  # id IN (1, 2, 3)

    # БОЛЬШЕ / МЕНЬШЕ
    gt_books = Book.objects.filter(price__gt=100)  # price > 100
    gte_books = Book.objects.filter(price__gte=100)  # price >= 100
    lt_books = Book.objects.filter(price__lt=50)  # price < 50
    lte_books = Book.objects.filter(price__lte=50)  # price <= 50

    # ДИАПАЗОН (BETWEEN)
    range_books = Book.objects.filter(published_at__range=('1990-01-01', '2000-12-31'))
    # published_at BETWEEN '1990-01-01' AND '2000-12-31'

    # NULL / NOT NULL
    null_books = Book.objects.filter(category__isnull=True)  # category IS NULL
    not_null_books = Book.objects.filter(category__isnull=False)  # category IS NOT NULL

    # РЕГУЛЯРНЫЕ ВЫРАЖЕНИЯ (PostgreSQL: ~, SQLite: REGEXP)
    regex_books = Book.objects.filter(title__regex=r'^The.*$')  # title ~ '^The.*$'
    iregex_books = Book.objects.filter(title__iregex=r'^the.*$')  # title ~* '^the.*$'

    # СЛОЖНЫЕ УСЛОВИЯ: Q-объекты (логика И/ИЛИ/НЕ)
    q_books = Book.objects.filter(
        Q(title__icontains='война') | Q(author__icontains='толстой'),  # ИЛИ
        published_at__year__gte=1800,  # И
        ~Q(in_stock=False)  # НЕ (эквивалент in_stock=True)
    )

# === 3. СОРТИРОВКА ===
    ordered_books = Book.objects.order_by('title')  # ASC по title
    reverse_ordered = Book.objects.order_by('-price')  # DESC по price
    multi_ordered = Book.objects.order_by('author', '-published_at')  # сначала автор, потом дата (обратно)

# === 4. ОГРАНИЧЕНИЯ (пагинация, срезы) ===
    first_10 = Book.objects.all()[:10]  # LIMIT 10
    page_2 = Book.objects.all()[10:20]  # OFFSET 10 LIMIT 10
    first_book = Book.objects.first()  # первый или None
    last_book = Book.objects.order_by('id').last()  # последний (требует order_by!)

# === 5. ВЫБОР ПОЛЕЙ (оптимизация передачи данных) ===
    only_title_author = Book.objects.only('title', 'author')  # загружать ТОЛЬКО эти поля
    defer_desc = Book.objects.defer('description')  # НЕ загружать description
    as_dicts = Book.objects.values('id', 'title')  # [{'id': 1, 'title': '...'}]
    as_flat_list = Book.objects.values_list('id', flat=True)  # [1, 2, 3, ...]
    as_tuple_list = Book.objects.values_list('id', 'title')  # [(1, '...'), (2, '...')]

# === 6. ОПТИМИЗАЦИЯ ЗАПРОСОВ (JOIN'ы) ===
    # Для ForeignKey / OneToOne
    with_author = Book.objects.select_related('category')  # JOIN category (один запрос)

    # Для ManyToMany / reverse ForeignKey
    # with_reviews = Book.objects.prefetch_related('reviews')  # отдельный запрос для связанных

# === 7. АННОТАЦИИ (Добавляет вычисляемое поле к КАЖДОМУ объекту) ===
    annotated_books = Book.objects.annotate(
        title_upper=Upper('title'),  # title_upper = UPPER(title)
        title_lower=Lower('title'),
        author_title=Concat('author', Value(' - '), 'title'),
        review_count=Count('reviews'),  # если есть related_name='reviews'
        avg_rating=Avg('reviews__rating'),  # через связь
        price_doubled=F('price') * 2  # F-выражения: операции в БД
    )

    # Пример: выбрать книги с более чем 5 отзывами
    popular_books = Book.objects.annotate(
        review_count=Count('reviews')
    ).filter(review_count__gt=5)

# === 8. АГРЕГАЦИЯ (Вычисляет итоговое значение по ВСЕМУ QuerySet) ===
    stats = Book.objects.aggregate(
        total_books=Count('id'),
        avg_price=Avg('price'),
        max_price=Max('price'),
        min_price=Min('price'),
        total_value=Sum('price')
    )
    # Результат: {'total_books': 120, 'avg_price': 450.5, ...}

# === 9. ПРОВЕРКИ (без загрузки объектов) ===
     has_books = Book.objects.exists()  # SELECT 1 ... LIMIT 1 → True/False
     count = Book.objects.count()  # SELECT COUNT(*) → число

# === 10. МАССОВЫЕ ОПЕРАЦИИ (без вызова save()) ===
     Book.objects.filter(price__lt=100).update(in_stock=False)  # массовое обновление
     Book.objects.filter(published_at__year__lt=1900).delete()  # массовое удаление

# === 11. ПОЛУЧЕНИЕ ОДНОГО ОБЪЕКТА ===
    one_book = get_object_or_404(Book, pk=1)  # стандартный способ
    or:
    try:
        one_book = Book.objects.get(title='1984')
    except Book.DoesNotExist:
        one_book = None

# === 12. КОНТЕКСТ ДЛЯ ШАБЛОНА ===
    context = {
        # Вы можете передать любой QuerySet — он выполнится при рендеринге
        'books': Book.objects.all(),

        # Или передать уже выполненные данные (если нужно использовать .count(), .exists() и т.д.)
        'stats': stats,
        'has_books': has_books,
        'total_count': count,

        # Пример: популярные книги с аннотациями
        'popular_books': popular_books[:5],

        # Пример: первая книга из списка
        'featured_book': Book.objects.first(),
    }

    return render(request, 'books/demo.html', context)



#================   ЧТО ПЕРЕДАЕМ В ШАБЛОН ===========================

def book_list(request):
    books = Book.objects.annotate(review_count=Count('reviews'))
    return render(request, 'books/list.html', {'books': books})


{ % for book in books %}
    < div >
       < h3 > {{book.title}} < / h3 >
       < p > Автор: {{book.author}} < / p >
       < p > Отзывов: {{book.review_count}} < / p > <!-- ← это из annotate! -->

        { % if book.review_count > 10 %}
        < span class ="popular" > 🔥 Популярная! < / span >

        { % endif %}
    < / div >
{ % endfor %}

#То есть по сути я передам объект  "books"  в шаблон, но использую review_count (и другие поля, если они там будут)