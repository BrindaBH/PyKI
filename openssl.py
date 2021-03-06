from subprocess import check_output, Popen, CalledProcessError, PIPE
import os

# TODO Move to configuration file
__OpenSSLBin = '/usr/bin/openssl'
__OpenSSLConfig = 'conf/CA/ca-sign.conf'
__x509Extensions = {
    'sslserver': """
        basicConstraints = critical, CA:FALSE
        extendedKeyUsage = critical, serverAuth, clientAuth
        subjectAltName = DNS:{0},DNS:www.{0}
        crlDistributionPoints = URI:http://pyki.ettoredelnegro.me/pyki.crl
        authorityInfoAccess = caIssuers;URI:http://pyki.ettoredelnegro.me/pyki.crt
    """,
    'smime': """
        basicConstraints = CA:FALSE
        extendedKeyUsage = critical, emailProtection
        subjectAltName = email:{0}
        crlDistributionPoints = URI:http://pyki.ettoredelnegro.me/pyki.crl
        authorityInfoAccess = caIssuers;URI:http://pyki.ettoredelnegro.me/pyki.crt
    """,
    'codesign': """
        basicConstraints = CA:FALSE
        extendedKeyUsage = critical, codeSigning
        crlDistributionPoints = URI:http://pyki.ettoredelnegro.me/pyki.crl
        authorityInfoAccess = caIssuers;URI:http://pyki.ettoredelnegro.me/pyki.crt
    """
}


def signSPKAC(SPKAC, certificateType, serial, email=None, DNS=None, CN=None, O=None, L=None, C=None):
    # SSL Server
    if certificateType == 'sslserver':
        if not DNS:
            raise Exception('DNS cannot be null when requesting an SSL server certificate')
            # Force CN = DNS
        CN = DNS

    # S/MIME
    elif certificateType == 'smime':
        if not email:
            raise Exception('email cannot be null when requesting an S/MIME certificate')
            # Force CN = email
        CN = email

    # Generate SPKAC text file
    spkacFile = open('tmp/spkac.txt', 'w')
    spkacRequest = 'SPKAC={}\nCN={}\nO={}\nL={}\nC={}'.format(SPKAC, CN, O, L, C)
    spkacFile.write(spkacRequest)
    spkacFile.close()

    # Generate extensions file
    extFile = open('tmp/extensions.conf', 'w')
    extFile.write(__x509Extensions[certificateType].format(CN))
    extFile.close()

    # Clear CA database
    # try:
    #     os.remove('conf/CA/index.txt.attr')
    #     os.remove('conf/CA/index.txt.old')
    #     os.remove('conf/CA/serial.old')
    # except FileNotFoundError as e:
    #     print(e)
    serialFile = open('conf/CA/serial', 'w')
    serialFile.write(serial + '\n')
    serialFile.close()
    # indexFile = open('conf/CA/index.txt', 'w')
    # indexFile.write('')
    # indexFile.close()

    # Sign the request
    try:
        check_output([__OpenSSLBin, 'ca',
                      '-config', __OpenSSLConfig,
                      '-spkac', 'tmp/spkac.txt',
                      '-batch',
                      '-extfile', 'tmp/extensions.conf'])
    except CalledProcessError as e:
        print(e.output)
        raise e

    # Extract certificate from PEM file
    certFile = open('conf/CA/newcerts/' + serial + '.pem', 'r')
    lines = certFile.readlines()
    certFile.close()
    PEMCert = ''
    beginCert = False
    for line in lines:
        if line == '-----BEGIN CERTIFICATE-----\n':
            beginCert = True
        if beginCert:
            PEMCert += line

    return PEMCert


def x509SubjectHash(PEMCert):
    # Converts the PEM certificate string into a byte sequence
    PEMCert = bytes(PEMCert, 'utf-8')

    try:
        proc = Popen([__OpenSSLBin, 'x509',
                      '-subject_hash',
                      '-noout'],
                     stdin=PIPE, stdout=PIPE)

        # Returns a tuple (stdoutdata, stderrdata)
        output = proc.communicate(input=PEMCert)[0]
        certHash = str(output, 'utf-8')
    except CalledProcessError as e:
        print(e.output)
        raise e

    # Check return code
    if proc.returncode != 0:
        raise Exception("Error executing OpenSSL")

    return certHash


def x509Fingerprint(PEMCert):
    # Converts the PEM certificate string into a byte sequence
    PEMCert = bytes(PEMCert, 'utf-8')

    try:
        proc = Popen([__OpenSSLBin, 'x509',
                      '-fingerprint',
                      '-noout'],
                     stdin=PIPE, stdout=PIPE)

        # Returns a tuple (stdoutdata, stderrdata)
        output = proc.communicate(input=PEMCert)[0]
        certFingerptin = str(output, 'utf-8')
    except CalledProcessError as e:
        print(e.output)
        raise e

    # Check return code
    if proc.returncode != 0:
        raise Exception("Error executing OpenSSL")

    return certFingerptin
