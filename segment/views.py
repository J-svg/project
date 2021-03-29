from django.shortcuts import render
from .forms import ImageForm
import cv2, os
import numpy as np
import concurrent.futures
from .models import Image
import re

IMAGE_FILE_TYPES = ['png', 'jpg', 'jpeg']
IMAGE_PATH = 'segment/static/segment/images/'

def homepage(request):
    if request.method == "POST":
        Image.objects.all().delete()
        delete_static()
        form = ImageForm(request.POST, request.FILES)
        file_name = str(request.FILES['photo'])
        s = file_name.split('.')
        print(s)
        file_type = str(request.FILES['photo']).split('.')[-1]
        if file_type not in IMAGE_FILE_TYPES:
            return render(request, 'segment/home.html', {'form': form, })

        if form.is_valid():
            form.save()
            file_name = re.sub(' ', '_', file_name)
            file_name = re.sub('(\(|\)|\@|\$|\#|\%|\^|\&|!)', '', file_name)
            file_path = 'media/upload/'+file_name

            # image_processing(file_path)
            with concurrent.futures.ThreadPoolExecutor() as executor:
                k_val = [2, 5, 8, 16, 32]
                results = []
                for k in k_val:
                    argument = [file_path, k]
                    p = executor.submit(image_processing, *argument)
                    results.append(p)

                ko = [0, 1, 2, 3, 4]
                for count, f in enumerate(concurrent.futures.as_completed(results)):
                    ko[count] = f.result()

            print(ko)
            original = Image.objects.all()

            return render(request, 'segment/test.html', {'form': form, 'original': original, 'k2': ko[0], 'k5': ko[1], 'k8': ko[2], 'k16': ko[3], 'k32': ko[4]})
    form = ImageForm()
    return render(request, 'segment/home.html', {'form': form})


def image_processing(file_path, k):
    print(file_path)
    img = cv2.imread(file_path)

    if img is None:
        img = cv2.imread('segment/static/segment/images/No_Image_Available.jpg')

    r = 400/img.shape[0]
    dim = (int(img.shape[1]*r), 400)

    img = cv2.resize(img, dim, interpolation=cv2.INTER_NEAREST)

    img2 = img.reshape((-1, 3))
    img2 = np.float32(img2)
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)

    attempts = 2
    ret, label, center = cv2.kmeans(img2, k, None, criteria, attempts, cv2.KMEANS_RANDOM_CENTERS)

    center = np.uint8(center)

    centroid = [tuple(c)[::-1] for c in center]

    res = center[label.flatten()]
    res2 = res.reshape((img.shape))
    path = IMAGE_PATH+'segment'+str(k)+'.png'
    # path = IMAGE_PATH + 'segment.png'
    cv2.imwrite(path, res2)
    return centroid

def delete_static():
    folder = "media/upload"
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


