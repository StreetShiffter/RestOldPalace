
# ======= Простой GET — отображение списка объектов (аналог ListView)
from django.shortcuts import render
from .models import Book

def book_list(request):
    # QuerySet — ленивый, не выполняется до итерации
    books = Book.objects.all()  # это QuerySet

    # Контекст — словарь, передаётся в шаблон
    context = {
        'books': books,
        'title': 'Список книг'
    }
    return render(request, 'books/list.html', context)

# ======= GET — детальная страница (аналог DetailView)
from django.shortcuts import get_object_or_404

def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)
    return render(request, 'books/detail.html', {'book': book})

# ======= Post запрос с заранее созданной формой (аналог CreatelView)
from django import forms
from .models import Book

class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = ['title', 'author']

def book_create(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()  # ← создаёт и сохраняет объект
            return redirect('book_list')
    else:
        form = BookForm()  # пустая форма для GET

    return render(request, 'books/form.html', {'form': form})

# ======= Post запрос  (аналог DeletelView)
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.delete()
        return redirect('book_list')
    return render(request, 'books/confirm_delete.html', {'book': book})


# ======= POST/GET — редактирование объекта (аналог UpdateView)
from django.shortcuts import render, get_object_or_404, redirect


def book_update(request, pk):
    book = get_object_or_404(Book, pk=pk)

    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)  # ← передаём instance для автозаполнения формы готовыми данными из БД!
        if form.is_valid():
            form.save()  # обновит существующий объект
            return redirect('book_detail', pk=book.pk)
    else:
        form = BookForm(instance=book)  # ← заполняет форму данными объекта

    return render(request, 'books/form.html', {'form': form, 'book': book})