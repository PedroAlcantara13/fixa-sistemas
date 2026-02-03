<?php

/*************************
 * FUNÇÕES E CONFIGURAÇÕES
 *************************/
function carregarJson($path) {
    if (!file_exists($path)) {
        return [];
    }
    $data = json_decode(file_get_contents($path), true);
    return is_array($data) ? $data : [];
}

$dddParaUf = [
    '11'=>'SP','12'=>'SP','13'=>'SP','14'=>'SP','15'=>'SP','16'=>'SP','17'=>'SP','18'=>'SP','19'=>'SP',
    '21'=>'RJ','22'=>'RJ','24'=>'RJ',
    '27'=>'ES','28'=>'ES',
    '31'=>'MG','32'=>'MG','33'=>'MG','34'=>'MG','35'=>'MG','37'=>'MG','38'=>'MG',
    '41'=>'PR','42'=>'PR','43'=>'PR','44'=>'PR','45'=>'PR','46'=>'PR',
    '47'=>'SC','48'=>'SC','49'=>'SC',
    '51'=>'RS','53'=>'RS','54'=>'RS','55'=>'RS',
    '61'=>'DF',
    '62'=>'GO','64'=>'GO',
    '63'=>'TO',
    '65'=>'MT','66'=>'MT',
    '67'=>'MS',
    '68'=>'AC',
    '69'=>'RO',
    '71'=>'BA','73'=>'BA','74'=>'BA','75'=>'BA','77'=>'BA',
    '79'=>'SE',
    '81'=>'PE','87'=>'PE',
    '82'=>'AL',
    '83'=>'PB',
    '84'=>'RN',
    '85'=>'CE','88'=>'CE',
    '86'=>'PI','89'=>'PI',
    '91'=>'PA','93'=>'PA','94'=>'PA',
    '92'=>'AM','97'=>'AM',
    '95'=>'RR',
    '96'=>'AP',
    '98'=>'MA','99'=>'MA',
];

$jsonPath = __DIR__ . '/portab.json';
$jsonData = carregarJson($jsonPath);

/*************************
 * OPERADORAS (DINÂMICAS)
 *************************/
$operadoras = [];
foreach ($jsonData as $item) {
    $operadoras[$item['Operadora']] = true;
}
ksort($operadoras);

/*************************
 * PROCESSAMENTO
 *************************/
$resultado = '';
$erro = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {

    $ntl = preg_replace('/\D/', '', $_POST['ntl'] ?? '');
    $operadoraEscolhida = $_POST['operadora'] ?? '';

    if (strlen($ntl) < 10) {
        $erro = 'NTL inválido';
    } else {

        $ddd = substr($ntl, 0, 2);

        if (!isset($dddParaUf[$ddd])) {
            $erro = "DDD {$ddd} não mapeado";
        } else {

            $uf = $dddParaUf[$ddd];
            $config = null;

            foreach ($jsonData as $item) {
                if (
                    strcasecmp($item['Operadora'], $operadoraEscolhida) === 0 &&
                    $item['UF'] === $uf
                ) {
                    $config = $item;
                    break;
                }
            }

            if (!$config) {
                $erro = "Configuração não encontrada para {$operadoraEscolhida} / {$uf}";
            } else {

                $cdo = $config['CDO'];
                $rnpCsp = str_pad((string)$config['RNP/CSP'], 5, '0', STR_PAD_LEFT);

                $rnp  = substr($rnpCsp, 0, 3);
                $csp  = substr($rnpCsp, 2, 3);
                $csp1  = substr($rnpCsp, 3, 2);
                $rand = $csp;

                $nue = "E{$rand}{$ntl}";

                $resultado1 ="CNTLPO:ISV=portab,NTL=\"{$ntl}\",EIP=S_INF,RNP=\"{$rnp}\",CSP={$csp1},CNL=S_INF,NUE=\"{$nue}\",NUF=S_INF,TBR=1,TPB=PREST;\n";
                $resultado2 ="MNTLPO:ISV=portab,NTL=\"{$ntl}\",CDO=\"00{$cdo}\";";
            }
        }
    }
}
?>

<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Gerador de Portabilidade</title>
<link rel="stylesheet" href="style.css">
</head>
<body>

<div class="container">
<img class="img" src="Geomago.jpeg" alt="Geomago">
<h1>The Mage Portab</h1>

<form method="POST">
    <label>NTL</label>
    <input name="ntl" value="<?= htmlspecialchars($_POST['ntl'] ?? '') ?>" placeholder="Ex: 86996474805">

    <label>Operadora</label>
    <select name="operadora">
        <option value="">Selecione</option>
        <?php foreach ($operadoras as $op => $_): ?>
            <option value="<?= htmlspecialchars($op) ?>"
                <?= ($op === ($_POST['operadora'] ?? '')) ? 'selected' : '' ?>>
                <?= htmlspecialchars($op) ?>
            </option>
        <?php endforeach; ?>
    </select>

    <button>Gerar Comandos</button>
</form>

<?php if ($erro): ?>
    <div class="erro"><?= htmlspecialchars($erro) ?></div>
<?php endif; ?>

<?php if ($resultado1): ?>
    <div class="resultado"><?= htmlspecialchars($resultado1) ?></div>
<?php endif; ?>
<?php if ($resultado2): ?>
    <div class="resultado"><?= htmlspecialchars($resultado2) ?></div>
<?php endif; ?>

<div class="footer">Sistema Interno • Portabilidade SMP</div>
<div class="footer">Desenvolvido por: Pedro Alcantara</div>
</div>

</body>
</html>