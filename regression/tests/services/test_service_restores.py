import time
import os
import hashlib
import requests

from ..utils import tunnel_url


def get_hash(path):
    # Specify how many bytes of the file you want to open at a time
    BLOCKSIZE = 65536

    sha = hashlib.sha256()
    with open(path, 'rb') as kali_file:
        file_buffer = kali_file.read(BLOCKSIZE)
        while len(file_buffer) > 0:
            sha.update(file_buffer)
            file_buffer = kali_file.read(BLOCKSIZE)

    return sha.hexdigest()



def test_customer_1_upload_download_file_with_master():
    shared_volume = '/customer_1'
    origin_filename = 'file_customer_1.txt'

    directory_local_file = '%s/%s' % (shared_volume, origin_filename)

    key_id = 'master$customer_1@is_8084'
    virtual_file = 'virtual_file.txt'

    remote_path = '%s:%s' % (key_id, virtual_file)

    download_volume = '/customer_1'

    directory_dowloaded_file = '%s/%s' % (download_volume, virtual_file)

    assert not os.path.exists(directory_dowloaded_file)

    for i in range(1):
        response = requests.post(url=tunnel_url('customer_1', 'file/create/v1'), json={'remote_path': remote_path}, )
        assert response.status_code == 200
        if response.json()['status'] == 'OK':
            break
        # assert response.json()['status'] == 'OK', response.json()
    else:
        assert response.json()['status'] == 'OK', response.json()

    response = requests.post(
        url=tunnel_url('customer_1', 'file/upload/start/v1'),
        json={'remote_path': remote_path, 'local_path': directory_local_file, 'wait_result': 'true'}
    )
    assert response.status_code == 200
    assert response.json()['status'] == 'OK', response.json()

    for i in range(20):
        response = requests.post(
            url=tunnel_url('customer_1', 'file/download/start/v1'),
            json={'remote_path': remote_path, 'destination_folder': download_volume, 'wait_result': 'true'}
        )
        assert response.status_code == 200

        if response.json()['status'] == 'OK':
            break

        if response.json()['errors'][0].startswith('download not possible, uploading'):
            print('file is not ready for download: retry again in 1 sec')
            time.sleep(1)
        else:
            print(response.json())
            assert False, response.json()

    else:
        print('download was not successful')
        assert False, response.json()

    assert os.path.exists(directory_dowloaded_file)

    assert get_hash(directory_local_file) == get_hash(directory_dowloaded_file)
